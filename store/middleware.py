"""
store/middleware.py

Two middleware classes:
  1. RateLimitMiddleware  — in-memory sliding-window rate limiter for bid and enquiry endpoints
  2. SecurityHeadersMiddleware — adds CSP and other security headers to every response
"""
import time
import logging
from collections import defaultdict
from threading import Lock
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

security_log = logging.getLogger('store.security')


# ── In-memory rate limit store ─────────────────────────────────────────────────
# Structure: { (ip, endpoint_key): [timestamp, timestamp, ...] }
_rate_store: dict = defaultdict(list)
_rate_lock = Lock()


def _is_rate_limited(ip: str, key: str, max_calls: int, window_secs: int) -> bool:
    """
    Sliding window rate limiter.
    Returns True if the caller has exceeded max_calls within window_secs.
    Thread-safe via a module-level lock.
    """
    now = time.time()
    store_key = (ip, key)

    with _rate_lock:
        # Prune timestamps outside the window
        _rate_store[store_key] = [t for t in _rate_store[store_key] if now - t < window_secs]
        count = len(_rate_store[store_key])

        if count >= max_calls:
            return True

        _rate_store[store_key].append(now)
        return False


def _get_client_ip(request) -> str:
    """Extract real client IP, respecting X-Forwarded-For in production."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limits:
      - POST /auctions/<slug>/bid/   → BID limits
      - POST /enquiry/               → ENQUIRY limits
    Returns 429 JSON for AJAX, or a plain 429 for form posts.
    """

    BID_PATH_SUFFIX = '/bid/'
    ENQUIRY_PATH = '/enquiry/'

    def process_request(self, request):
        if request.method != 'POST':
            return None

        path = request.path
        ip = _get_client_ip(request)

        # ── Bid endpoint ──────────────────────────────────────────────────────
        if path.startswith('/auctions/') and path.endswith(self.BID_PATH_SUFFIX):
            max_calls = getattr(settings, 'RATE_LIMIT_BID_MAX', 10)
            window = getattr(settings, 'RATE_LIMIT_BID_WINDOW', 60)
            key = f'bid:{path}'

            if _is_rate_limited(ip, key, max_calls, window):
                security_log.warning('Rate limit hit — bid | ip=%s path=%s', ip, path)
                return JsonResponse(
                    {'success': False,
                     'error': f'Too many bids. Please wait {window} seconds before trying again.'},
                    status=429
                )

        # ── Enquiry endpoint ──────────────────────────────────────────────────
        elif path == self.ENQUIRY_PATH:
            max_calls = getattr(settings, 'RATE_LIMIT_ENQUIRY_MAX', 5)
            window = getattr(settings, 'RATE_LIMIT_ENQUIRY_WINDOW', 300)
            key = 'enquiry'

            if _is_rate_limited(ip, key, max_calls, window):
                security_log.warning('Rate limit hit — enquiry | ip=%s', ip)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'success': False,
                         'error': 'Too many submissions. Please try again later.'},
                        status=429
                    )
                from django.http import HttpResponse
                return HttpResponse('Too many requests. Please try again later.', status=429)

        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds security-related HTTP response headers to every response.
    Django handles X-Frame-Options and X-Content-Type-Options via settings;
    this adds CSP and Referrer-Policy which Django does not cover natively.
    """

    def process_response(self, request, response):
        # Content Security Policy
        # - Tailwind is loaded from cdn.tailwindcss.com
        # - Google Fonts from fonts.googleapis.com / fonts.gstatic.com
        # - WhatsApp redirects are external navigations (no script/frame needed)
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        # Belt-and-braces even though Django settings also set these
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        return response
