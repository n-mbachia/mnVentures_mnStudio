"""
Django settings for MN Ventures Furniture Store
"""

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Core ──────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'django_celery_beat',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'store.middleware.RateLimitMiddleware',
    'store.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'mnventures.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'mnventures.wsgi.application'

# ── Database ──────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='mnVenturesStudio_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {'connect_timeout': 10},
    }
}

# ── Password Validation ───────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Localization ──────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ── Static & Media ────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Security (Sessions & CSRF) ────────────────────────────
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://127.0.0.1:8000'
).split(',')

# ── Production Security ───────────────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ── Rate Limiting ─────────────────────────────────────────
RATE_LIMIT_BID_MAX = config('RATE_LIMIT_BID_MAX', default=10, cast=int)
RATE_LIMIT_BID_WINDOW = config('RATE_LIMIT_BID_WINDOW', default=60, cast=int)
RATE_LIMIT_ENQUIRY_MAX = config('RATE_LIMIT_ENQUIRY_MAX', default=5, cast=int)
RATE_LIMIT_ENQUIRY_WINDOW = config('RATE_LIMIT_ENQUIRY_WINDOW', default=300, cast=int)

# ── Auction Settings ──────────────────────────────────────
AUCTION_SNIPE_WINDOW = config('AUCTION_SNIPE_WINDOW', default=120, cast=int)
AUCTION_SNIPE_EXTENSION = config('AUCTION_SNIPE_EXTENSION', default=120, cast=int)
AUCTION_MAX_EXTENSIONS = config('AUCTION_MAX_EXTENSIONS', default=5, cast=int)
AUCTION_MAX_BIDS_PER_BIDDER = config('AUCTION_MAX_BIDS_PER_BIDDER', default=20, cast=int)

# ── M-Pesa ────────────────────────────────────────────────
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='247247')
MPESA_ACCOUNT_NUMBER = config('MPESA_ACCOUNT_NUMBER', default='')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')
MPESA_SANDBOX = config('MPESA_SANDBOX', default=True, cast=bool)

# ── Email ─────────────────────────────────────────────────
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='MN Studio <noreply@your-domain-name.co.ke>'
)

# ── Business Settings ─────────────────────────────────────
WHATSAPP_NUMBER = config('WHATSAPP_NUMBER', default='')
BUSINESS_NAME = config('BUSINESS_NAME', default='MN Ventures')
BUSINESS_LOCATION = config('BUSINESS_LOCATION', default='Kenya')
CURRENCY_SYMBOL = 'Kes'
VAT_RATE_DISPLAY = '16%'
VAT_REGISTRATION = config('VAT_REGISTRATION', default='')

# ── Logging ───────────────────────────────────────────────
(BASE_DIR / 'logs').mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'},
        'simple': {'format': '{levelname}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING'},
    },
}

# ── Celery / Redis ────────────────────────────────────────
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


CSP_STYLE_SRC = [
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
    "https://cdnjs.cloudflare.com",  # Required for Font Awesome CSS
]

CSP_FONT_SRC = [
    "'self'",
    "https://fonts.gstatic.com",
    "https://cdnjs.cloudflare.com", # Required for the actual icon webfonts[cite: 1]
]

# ── Site URL ──────────────────────────────────────────────
SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000')
