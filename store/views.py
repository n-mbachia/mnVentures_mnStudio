"""
store/views.py — MN Ventures complete view layer
"""
import logging
import urllib.parse
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import (AuctionItem, AuctionSecurityEvent, Bid, BidderProfile,
                     Category, Enquiry, MpesaPayment, ProxyBid, Product)
from .forms import EnquiryForm

auction_log  = logging.getLogger('store.auctions')
security_log = logging.getLogger('store.security')
payment_log  = logging.getLogger('store.payments')


def _get_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')

def _wa_num() -> str:
    return settings.WHATSAPP_NUMBER.replace('+', '').replace(' ', '')


# ── STORE VIEWS ────────────────────────────────────────────────────────────────

def home(request):
    categories   = Category.objects.all()
    all_products = Product.objects.filter(is_available=True)
    category_slug = request.GET.get('category', '')
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        if selected_category:
            all_products = all_products.filter(category=selected_category)
    products_page = Paginator(all_products, 9).get_page(request.GET.get('page'))

    for a in AuctionItem.objects.exclude(status__in=['closed', 'cancelled']):
        a.refresh_status()

    return render(request, 'store/home.html', {
        'categories':        categories,
        'products':          products_page,
        'selected_category': selected_category,
        'live_auctions':     AuctionItem.objects.filter(status='live').select_related('product')[:3],
        'upcoming_auctions': AuctionItem.objects.filter(status='upcoming').select_related('product')[:3],
        'whatsapp_number':   _wa_num(),
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related = Product.objects.filter(category=product.category, is_available=True).exclude(pk=product.pk)[:4]
    wa_msg  = urllib.parse.quote(product.whatsapp_message())
    return render(request, 'store/product_detail.html', {
        'product': product, 'related_products': related,
        'wa_link': f"https://wa.me/{_wa_num()}?text={wa_msg}",
    })


def about(request):
    return render(request, 'store/about.html')


def terms(request):
    return render(request, 'store/terms.html')


def privacy(request):
    return render(request, 'store/privacy.html')


@require_POST
def enquiry(request):
    form = EnquiryForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        pid = request.POST.get('product_id')
        if pid:
            obj.product = Product.objects.filter(pk=pid).first()
        obj.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Thank you! We will contact you soon.'})
        return render(request, 'store/enquiry_success.html')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return render(request, 'store/home.html', {'enquiry_form': form})


def product_api(request):
    qs = Product.objects.filter(is_available=True)
    cat = request.GET.get('category', '')
    if cat:
        qs = qs.filter(category__slug=cat)
    data = []
    for p in qs:
        wa_msg = urllib.parse.quote(p.whatsapp_message())
        data.append({
            'id': p.pk, 'name': p.name, 'slug': p.slug,
            'category': p.category.name if p.category else '',
            'short_description': p.short_description,
            'price': p.formatted_price(), 'badge': p.badge,
            'image': p.image.url if p.image else '',
            'wa_link': f"https://wa.me/{_wa_num()}?text={wa_msg}",
        })
    return JsonResponse({'products': data})


# ── BIDDER DASHBOARD ───────────────────────────────────────────────────────────

def my_bids(request):
    """
    Allow a bidder to look up their bid history by phone number.
    No login required — identified by phone.
    """
    phone   = request.GET.get('phone', '').strip().replace(' ', '')
    bidder  = None
    bids    = []
    won     = []

    if phone:
        bidder = BidderProfile.objects.filter(phone=phone).first()
        if bidder:
            bids = Bid.objects.filter(bidder=bidder, is_valid=True).select_related('auction__product').order_by('-placed_at')[:50]
            won  = AuctionItem.objects.filter(winner=bidder).select_related('product')

    return render(request, 'store/my_bids.html', {
        'phone': phone, 'bidder': bidder, 'bids': bids, 'won': won,
    })


# ── AUCTION VIEWS ──────────────────────────────────────────────────────────────

def auction_list(request):
    for a in AuctionItem.objects.exclude(status__in=['closed', 'cancelled']):
        a.refresh_status()
    return render(request, 'store/auction_list.html', {
        'live_auctions':     AuctionItem.objects.filter(status='live').select_related('product'),
        'upcoming_auctions': AuctionItem.objects.filter(status='upcoming').select_related('product'),
        'closed_auctions':   AuctionItem.objects.filter(status='closed').select_related('product', 'winner')[:12],
    })


def auction_detail(request, slug):
    auction = get_object_or_404(AuctionItem, slug=slug)
    auction.refresh_status()
    AuctionItem.objects.filter(pk=auction.pk).update(views_count=auction.views_count + 1)
    bids    = auction.bids.filter(is_valid=True).select_related('bidder')[:20]
    wa_msg  = urllib.parse.quote(
        f"Hello MN Ventures! I'm interested in the auction for *{auction.product.name}*. "
        f"Current bid: {auction.formatted_price()}. Can you tell me more?"
    )
    get_token(request)   # ensure CSRF cookie is set for AJAX

    # Build winner WhatsApp link for server-rendered winner card
    wa_winner_link = ''
    if auction.status == 'closed' and auction.winner:
        winner_msg = urllib.parse.quote(
            f"🎉 Congratulations {auction.winner.name}! You won the MN Ventures auction for "
            f"*{auction.product.name}* with a winning bid of KSh {auction.winning_bid:,.0f}. "
            f"Please pay via M-Pesa Paybill 247247, Account 741222. "
            f"Reply here once paid and we will arrange delivery. Thank you!"
        )
        clean = auction.winner.phone.replace('+', '').replace(' ', '')
        wa_winner_link = f"https://wa.me/{clean}?text={winner_msg}"

    return render(request, 'store/auction_detail.html', {
        'auction':        auction,
        'bids':           bids,
        'wa_link':        f"https://wa.me/{_wa_num()}?text={wa_msg}",
        'wa_winner_link': wa_winner_link,
        'min_bid':        float(auction.minimum_next_bid),
    })


@require_POST
def place_bid(request, slug):
    """
    Security layers applied:
    1. CSRF — enforced by Django middleware (cookie set in auction_detail view)
    2. Rate limiting — handled by RateLimitMiddleware upstream
    3. Auction must be live — server-side re-check
    4. Amount parsed as Decimal — no floating point manipulation possible
    5. Minimum bid enforced inside a SELECT FOR UPDATE transaction
    6. Blocked bidder check
    7. Per-bidder bid cap
    8. Multiple phones from same IP — logged to AuctionSecurityEvent
    9. Anti-snipe extension
    10. Proxy bid engine triggered after every manual bid
    """
    ip         = _get_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:300]
    auction    = get_object_or_404(AuctionItem, slug=slug)
    auction.refresh_status()

    if auction.status != 'live':
        AuctionSecurityEvent.objects.create(
            auction=auction, event_type='auction_closed', ip_address=ip,
            detail=f'Bid attempted on {auction.status} auction'
        )
        return JsonResponse({'success': False, 'error': 'This auction is not currently live.'}, status=400)

    # Parse inputs
    phone      = request.POST.get('phone', '').strip().replace(' ', '')
    name       = request.POST.get('name', '').strip()
    email      = request.POST.get('email', '').strip()
    amount_raw = request.POST.get('amount', '').strip()

    if not phone or not name or not amount_raw:
        return JsonResponse({'success': False, 'error': 'Name, phone and bid amount are required.'}, status=400)
    if len(name) > 150 or len(phone) > 20:
        return JsonResponse({'success': False, 'error': 'Invalid input.'}, status=400)

    try:
        amount = Decimal(amount_raw).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        AuctionSecurityEvent.objects.create(
            auction=auction, event_type='invalid_amount', ip_address=ip, phone=phone,
            detail=f'Raw: {amount_raw!r}'
        )
        return JsonResponse({'success': False, 'error': 'Invalid bid amount.'}, status=400)

    if amount <= 0:
        return JsonResponse({'success': False, 'error': 'Bid must be positive.'}, status=400)

    # Get or create bidder
    bidder, _ = BidderProfile.objects.get_or_create(phone=phone, defaults={'name': name, 'email': email})
    if name:  bidder.name = name
    if email: bidder.email = email
    bidder.save(update_fields=['name', 'email'])

    if bidder.is_blocked:
        AuctionSecurityEvent.objects.create(
            auction=auction, event_type='blocked_bidder', ip_address=ip, phone=phone,
            detail=f'Blocked bidder id={bidder.pk}'
        )
        security_log.warning('Blocked bidder | phone=%s ip=%s', phone, ip)
        return JsonResponse({'success': False, 'error': 'Unable to place bid at this time.'}, status=403)

    max_bids = getattr(settings, 'AUCTION_MAX_BIDS_PER_BIDDER', 20)
    if auction.bids.filter(bidder=bidder, is_valid=True).count() >= max_bids:
        return JsonResponse({'success': False, 'error': f'Maximum {max_bids} bids per bidder reached.'}, status=400)

    # Log duplicate IP (shared network — don't block, just record)
    other_phones = (
        Bid.objects.filter(auction=auction, ip_address=ip, is_valid=True)
        .exclude(bidder=bidder).values_list('bidder__phone', flat=True).distinct()
    )
    if other_phones.exists():
        AuctionSecurityEvent.objects.create(
            auction=auction, event_type='duplicate_ip', ip_address=ip, phone=phone,
            detail=f'Same IP also has: {list(other_phones)}'
        )

    # Atomic bid with SELECT FOR UPDATE
    extended   = False
    proxy_bid  = None
    with transaction.atomic():
        locked = AuctionItem.objects.select_for_update().get(pk=auction.pk)
        locked.refresh_status()
        if locked.status != 'live':
            return JsonResponse({'success': False, 'error': 'Auction just closed.'}, status=400)
        if amount < locked.minimum_next_bid:
            return JsonResponse({'success': False, 'error': f'Minimum bid is {locked.formatted_price(locked.minimum_next_bid)}.'}, status=400)

        bid = Bid.objects.create(
            auction=locked, bidder=bidder, amount=amount,
            ip_address=ip, user_agent=user_agent, price_at_bid=locked.current_price,
        )
        auction_log.info('Bid placed | id=%s bidder=%s amount=%s', locked.pk, phone, amount)

        extended  = locked.apply_snipe_protection()
        proxy_bid = locked.process_proxy_bids(bid)

    # Notify MN Ventures via WhatsApp
    ext_note = f"\n⏱ Auction extended (#{locked.extension_count})" if extended else ''
    proxy_note = f"\n🤖 Proxy auto-bid: KSh {proxy_bid.amount:,.0f} by {proxy_bid.bidder.name}" if proxy_bid else ''
    wa_notify = urllib.parse.quote(
        f"🔔 New bid on *{auction.product.name}*!\n"
        f"Bidder: {bidder.name} ({bidder.phone})\n"
        f"Amount: KSh {amount:,.0f}\n"
        f"Total bids: {locked.bids.filter(is_valid=True).count()}"
        f"{ext_note}{proxy_note}"
    )

    leading_bid = locked.bids.filter(is_valid=True).order_by('-amount').first()
    is_leading  = leading_bid and leading_bid.bidder == bidder

    return JsonResponse({
        'success': True,
        'amount_formatted':     f"KSh {amount:,.0f}",
        'bid_count':            locked.bids.filter(is_valid=True).count(),
        'min_next_bid':         float(locked.minimum_next_bid),
        'min_next_bid_formatted': locked.formatted_price(locked.minimum_next_bid),
        'extended':             extended,
        'new_end_time':         locked.end_time.isoformat() if extended else None,
        'proxy_outbid':         proxy_bid is not None,
        'proxy_amount':         f"KSh {proxy_bid.amount:,.0f}" if proxy_bid else None,
        'is_leading':           is_leading and not proxy_bid,
        'notify_link':          f"https://wa.me/{_wa_num()}?text={wa_notify}",
    })


@require_POST
def set_proxy_bid(request, slug):
    """Set or update a proxy (maximum) bid for a bidder."""
    auction = get_object_or_404(AuctionItem, slug=slug)
    auction.refresh_status()

    if auction.status != 'live':
        return JsonResponse({'success': False, 'error': 'Auction is not live.'}, status=400)

    phone      = request.POST.get('phone', '').strip().replace(' ', '')
    amount_raw = request.POST.get('max_amount', '').strip()

    if not phone or not amount_raw:
        return JsonResponse({'success': False, 'error': 'Phone and max amount are required.'}, status=400)

    try:
        max_amount = Decimal(amount_raw).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid amount.'}, status=400)

    bidder = BidderProfile.objects.filter(phone=phone).first()
    if not bidder:
        return JsonResponse({'success': False, 'error': 'Phone not registered. Place a manual bid first.'}, status=400)

    if bidder.is_blocked:
        return JsonResponse({'success': False, 'error': 'Unable to set proxy bid.'}, status=403)

    if max_amount < auction.minimum_next_bid:
        return JsonResponse({'success': False,
                             'error': f'Proxy max must be at least {auction.formatted_price(auction.minimum_next_bid)}.'}, status=400)

    proxy, created = ProxyBid.objects.update_or_create(
        auction=auction, bidder=bidder,
        defaults={'max_amount': max_amount, 'is_active': True}
    )
    auction_log.info('Proxy bid set | bidder=%s max=%s auction=%s', phone, max_amount, auction.pk)

    return JsonResponse({
        'success': True,
        'max_amount': f"KSh {max_amount:,.0f}",
        'message': f"Proxy bid set — we'll automatically bid up to KSh {max_amount:,.0f} on your behalf.",
    })


@require_GET
def auction_status(request, slug):
    auction = get_object_or_404(AuctionItem, slug=slug)
    auction.refresh_status()

    top_bids = [
        {
            'bidder': b.bidder.name,
            'amount': f"KSh {b.amount:,.0f}",
            'time':   b.placed_at.strftime('%d %b %H:%M'),
            'proxy':  b.is_proxy,
        }
        for b in auction.bids.filter(is_valid=True).select_related('bidder')[:5]
    ]

    winner_data = None
    if auction.status == 'closed' and auction.winner:
        wa_msg = urllib.parse.quote(
            f"🎉 Congratulations {auction.winner.name}! You won the MN Ventures auction for "
            f"*{auction.product.name}* with a winning bid of KSh {auction.winning_bid:,.0f}.\n\n"
            f"To complete your purchase please send KSh {auction.winning_bid:,.0f} via M-Pesa:\n"
            f"Paybill: *247247*\nAccount: *741222*\n\n"
            f"Reply here once paid and we will arrange delivery. Thank you! 🛋️"
        )
        winner_data = {
            'name':    auction.winner.name,
            'phone':   auction.winner.phone,
            'amount':  f"KSh {auction.winning_bid:,.0f}",
            'wa_link': f"https://wa.me/{auction.winner.phone.replace('+','').replace(' ','')}?text={wa_msg}",
        }

    return JsonResponse({
        'status':            auction.status,
        'current_price':     f"KSh {auction.current_price:,.0f}",
        'current_price_raw': float(auction.current_price),
        'min_next_bid':      f"KSh {auction.minimum_next_bid:,.0f}",
        'min_next_bid_raw':  float(auction.minimum_next_bid),
        'bid_count':         auction.bid_count,
        'time_remaining':    auction.time_remaining_seconds,
        'end_time_iso':      auction.end_time.isoformat(),
        'extension_count':   auction.extension_count,
        'top_bids':          top_bids,
        'winner':            winner_data,
    })


# ── PAYMENT VIEWS ──────────────────────────────────────────────────────────────

@require_POST
def initiate_payment(request, slug):
    """Trigger M-Pesa STK push for auction deposit or winning bid."""
    from .mpesa import initiate_auction_payment, MpesaError

    auction      = get_object_or_404(AuctionItem, slug=slug)
    phone        = request.POST.get('phone', '').strip().replace(' ', '')
    payment_type = request.POST.get('payment_type', 'deposit')

    if not phone:
        return JsonResponse({'success': False, 'error': 'Phone number required.'}, status=400)

    bidder = BidderProfile.objects.filter(phone=phone).first()
    if not bidder:
        return JsonResponse({'success': False, 'error': 'Phone not registered. Place a bid first.'}, status=400)

    if payment_type == 'deposit':
        amount = auction.deposit_required
    elif payment_type == 'winning' and auction.winner == bidder:
        amount = auction.winning_bid
    else:
        return JsonResponse({'success': False, 'error': 'Invalid payment type.'}, status=400)

    if amount <= 0:
        return JsonResponse({'success': False, 'error': 'Nothing to pay.'}, status=400)

    try:
        payment = initiate_auction_payment(auction, bidder, amount, payment_type)
        return JsonResponse({
            'success': True,
            'message': f'M-Pesa prompt sent to {phone}. Enter your PIN to complete.',
            'reference': str(payment.reference),
            'paybill':   settings.MPESA_PAYBILL,
            'account':   settings.MPESA_ACCOUNT,
            'amount':    f"KSh {amount:,.0f}",
        })
    except MpesaError as e:
        payment_log.error('STK push failed | %s', e)
        return JsonResponse({
            'success': False,
            'error': f'M-Pesa error: {e}. Please pay manually: Paybill 247247, Account 741222.',
        }, status=502)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """
    Safaricom callback URL — receives payment confirmation.
    Must be exempt from CSRF (external POST from Safaricom).
    Secured by checking the originating IP in production (configure in Nginx).
    """
    import json
    from .mpesa import process_mpesa_callback

    try:
        data    = json.loads(request.body)
        payment = process_mpesa_callback(data)
        payment_log.info('Callback processed | ref=%s status=%s',
                         payment.reference if payment else '?',
                         payment.status if payment else '?')
    except Exception as e:
        payment_log.exception('Callback processing error: %s', e)

    # Always return 200 — Safaricom retries on anything else
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@require_GET
def payment_status(request, reference):
    """Poll payment status — called from the frontend after STK push."""
    try:
        payment = MpesaPayment.objects.get(reference=reference)
    except MpesaPayment.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)

    data = {
        'status':  payment.status,
        'amount':  f"KSh {payment.amount:,.0f}",
        'receipt': payment.mpesa_receipt_number,
    }
    if payment.is_paid and hasattr(payment, 'invoice'):
        data['invoice_number'] = payment.invoice.invoice_number

    return JsonResponse(data)


@require_GET
def invoice_view(request, reference):
    """Display invoice as HTML (print-friendly)."""
    try:
        payment = MpesaPayment.objects.get(reference=reference)
        invoice = payment.invoice
    except (MpesaPayment.DoesNotExist, Exception):
        from django.http import Http404
        raise Http404

    return render(request, 'store/invoice.html', {
        'invoice': invoice,
        'payment': payment,
    })


def sitemap(request):
    from django.http import HttpResponse
    products = Product.objects.filter(is_available=True)
    auctions = AuctionItem.objects.exclude(status='cancelled')
    site_url = settings.SITE_URL.rstrip('/')
    xml = render(request, 'store/sitemap.xml', {
        'products': products, 'auctions': auctions, 'site_url': site_url,
    })
    return HttpResponse(xml.content, content_type='application/xml')


def robots_txt(request):
    from django.http import HttpResponse
    site_url = settings.SITE_URL.rstrip('/')
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /my-bids/
Disallow: /payments/

Sitemap: {site_url}/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')
