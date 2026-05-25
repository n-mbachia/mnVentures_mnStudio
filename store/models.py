"""
store/models.py — MN Ventures complete data model
Covers: Products, Enquiries, Auctions, Bidding, Proxy Bids,
        M-Pesa Payments, VAT, Security Events
"""
import logging
import uuid
from decimal import Decimal
from django.db import models, transaction
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

auction_log  = logging.getLogger('store.auctions')
security_log = logging.getLogger('store.security')
payment_log  = logging.getLogger('store.payments')

VAT_RATE = Decimal('0.16')   # 16% VAT — Kenya


# ── HELPERS ────────────────────────────────────────────────────────────────────

def product_image_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f"products/{instance.slug or 'item'}.{ext}"


# ── STORE MODELS ───────────────────────────────────────────────────────────────

class Category(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    BADGE_CHOICES = [
        ('', 'None'), ('new', 'New'), ('bestseller', 'Best Seller'),
        ('sale', 'Sale'), ('limited', 'Limited'), ('custom', 'Custom'),
    ]
    category          = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name              = models.CharField(max_length=200)
    slug              = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    description       = models.TextField()
    price             = models.DecimalField(max_digits=10, decimal_places=2)
    image             = models.ImageField(upload_to=product_image_path, blank=True, null=True)
    badge             = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, default='')
    is_available      = models.BooleanField(default=True)
    is_featured       = models.BooleanField(default=False)
    show_price        = models.BooleanField(
        default=False,
        help_text='Display the price on the public storefront. '
                  'Leave unchecked for past commissions — "Enquire for pricing" will show instead.'
    )
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def formatted_price(self):
        return f"KSh {self.price:,.0f}"

    @property
    def image_url(self):
        """Return image URL or SVG placeholder data URI — never breaks in templates."""
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        return None   # template tag handles the placeholder

    def whatsapp_message(self):
        return (
            f"Hello MN Ventures! 🛋️ I'm interested in ordering the "
            f"*{self.name}* ({self.formatted_price()}). "
            f"Could you please provide more details and availability?"
        )

    def __str__(self):
        return self.name


class Enquiry(models.Model):
    STATUS_CHOICES = [('new', 'New'), ('contacted', 'Contacted'), ('closed', 'Closed')]
    product    = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='enquiries')
    name       = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20)
    email      = models.EmailField(blank=True)
    message    = models.TextField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Enquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.product or 'General'} ({self.created_at:%d %b %Y})"


# ── AUCTION MODELS ─────────────────────────────────────────────────────────────

class BidderProfile(models.Model):
    """Lightweight bidder — identified by phone number, no login required."""
    name       = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20, unique=True)
    email      = models.EmailField(blank=True)
    is_blocked = models.BooleanField(default=False, help_text='Block from placing bids')
    block_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def whatsapp_link(self):
        clean = self.phone.replace('+', '').replace(' ', '')
        return f"https://wa.me/{clean}"

    def normalise_phone(self):
        """Normalise to +254XXXXXXXXX format."""
        p = self.phone.strip().replace(' ', '').replace('-', '')
        if p.startswith('0') and len(p) == 10:
            p = '+254' + p[1:]
        elif p.startswith('254') and not p.startswith('+'):
            p = '+' + p
        self.phone = p


class AuctionItem(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'), ('live', 'Live'),
        ('closed', 'Closed'), ('cancelled', 'Cancelled'),
    ]

    product         = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='auction')
    slug            = models.SlugField(unique=True, blank=True)
    starting_price  = models.DecimalField(max_digits=10, decimal_places=2, help_text='Opening bid (KSh)')
    reserve_price   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                           help_text='Min sell price — hidden from bidders')
    bid_increment   = models.DecimalField(max_digits=8, decimal_places=2, default=500,
                                           help_text='Minimum raise per bid (KSh)')
    deposit_required = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                            help_text='M-Pesa deposit required to activate bidding (0 = none)')
    start_time      = models.DateTimeField()
    end_time        = models.DateTimeField()
    extension_count = models.PositiveSmallIntegerField(default=0)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    winner          = models.ForeignKey(BidderProfile, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='won_auctions')
    winning_bid     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description     = models.TextField(blank=True)
    terms           = models.TextField(blank=True, help_text='Auction-specific T&Cs')
    views_count     = models.PositiveIntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')
        if self.bid_increment and self.bid_increment < Decimal('100'):
            raise ValidationError('Bid increment must be at least KSh 100.')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.product.name) + '-auction'
        super().save(*args, **kwargs)

    # ── Status ────────────────────────────────────────────

    def refresh_status(self):
        now = timezone.now()
        changed = False
        if self.status == 'upcoming' and now >= self.start_time:
            self.status = 'live'
            changed = True
            auction_log.info('Auction OPENED | id=%s product="%s"', self.pk, self.product.name)
        if self.status == 'live' and now > self.end_time:
            self.status = 'closed'
            self._finalise()
            changed = True
        if changed:
            self.save(update_fields=['status', 'winner', 'winning_bid', 'end_time'])

    def _finalise(self):
        top = self.bids.filter(is_valid=True).order_by('-amount', 'placed_at').first()
        if top:
            if self.reserve_price is None or top.amount >= self.reserve_price:
                self.winner     = top.bidder
                self.winning_bid = top.amount
                top.is_winning  = True
                top.save(update_fields=['is_winning'])
                auction_log.info(
                    'Auction CLOSED winner=%s amount=%s | id=%s',
                    top.bidder.phone, top.amount, self.pk
                )
            else:
                auction_log.info('Auction CLOSED reserve not met | id=%s', self.pk)
        else:
            auction_log.info('Auction CLOSED no bids | id=%s', self.pk)

    def apply_snipe_protection(self):
        max_ext   = getattr(settings, 'AUCTION_MAX_EXTENSIONS',  5)
        window    = getattr(settings, 'AUCTION_SNIPE_WINDOW',   120)
        extension = getattr(settings, 'AUCTION_SNIPE_EXTENSION', 120)
        if self.extension_count >= max_ext:
            return False
        secs_left = (self.end_time - timezone.now()).total_seconds()
        if 0 < secs_left <= window:
            from datetime import timedelta
            self.end_time      += timedelta(seconds=extension)
            self.extension_count += 1
            self.save(update_fields=['end_time', 'extension_count'])
            auction_log.info('Snipe protection #%s | id=%s new_end=%s',
                             self.extension_count, self.pk, self.end_time)
            return True
        return False

    # ── Proxy bid engine ──────────────────────────────────

    def process_proxy_bids(self, new_bid):
        """
        After a manual bid is placed, check if any existing proxy bid
        would automatically outbid it. Returns the proxy Bid if triggered.
        """
        # Find the highest proxy that belongs to a different bidder and beats new_bid
        proxy = (
            ProxyBid.objects
            .filter(auction=self, is_active=True, max_amount__gt=new_bid.amount)
            .exclude(bidder=new_bid.bidder)
            .order_by('-max_amount', 'created_at')
            .first()
        )
        if not proxy:
            return None

        # The proxy auto-bids just enough to beat the new bid
        auto_amount = min(
            new_bid.amount + self.bid_increment,
            proxy.max_amount
        )
        auto_bid = Bid.objects.create(
            auction=self,
            bidder=proxy.bidder,
            amount=auto_amount,
            ip_address='proxy',
            user_agent='ProxyBidEngine',
            price_at_bid=new_bid.amount,
            is_proxy=True,
        )
        auction_log.info(
            'Proxy bid fired | proxy_bidder=%s amount=%s | id=%s',
            proxy.bidder.phone, auto_amount, self.pk
        )
        return auto_bid

    # ── VAT helpers ───────────────────────────────────────

    @property
    def current_price(self):
        top = self.bids.filter(is_valid=True).order_by('-amount', 'placed_at').first()
        return top.amount if top else self.starting_price

    @property
    def current_price_excl_vat(self):
        return (self.current_price / (1 + VAT_RATE)).quantize(Decimal('0.01'))

    @property
    def current_vat_amount(self):
        return (self.current_price - self.current_price_excl_vat).quantize(Decimal('0.01'))

    @property
    def bid_count(self):
        return self.bids.filter(is_valid=True).count()

    @property
    def minimum_next_bid(self):
        return self.current_price + self.bid_increment

    @property
    def is_live(self):
        now = timezone.now()
        return self.status == 'live' and self.start_time <= now <= self.end_time

    @property
    def time_remaining_seconds(self):
        return max(int((self.end_time - timezone.now()).total_seconds()), 0) if self.is_live else 0

    def formatted_price(self, amount=None):
        val = amount if amount is not None else self.current_price
        return f"KSh {val:,.0f}"

    def __str__(self):
        return f"Auction: {self.product.name} [{self.status}]"


class ProxyBid(models.Model):
    """
    A bidder's maximum — the system auto-bids on their behalf up to this amount.
    Only one active proxy per bidder per auction.
    """
    auction    = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='proxy_bids')
    bidder     = models.ForeignKey(BidderProfile, on_delete=models.CASCADE, related_name='proxy_bids')
    max_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                      help_text='Maximum the system will auto-bid on your behalf')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('auction', 'bidder')
        ordering = ['-max_amount']

    def __str__(self):
        return f"ProxyBid max=KSh{self.max_amount:,.0f} by {self.bidder.phone} on {self.auction}"


class Bid(models.Model):
    auction      = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='bids')
    bidder       = models.ForeignKey(BidderProfile, on_delete=models.CASCADE, related_name='bids')
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    is_valid     = models.BooleanField(default=True)
    is_winning   = models.BooleanField(default=False)
    is_proxy     = models.BooleanField(default=False, help_text='Placed automatically by proxy bid engine')
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    user_agent   = models.CharField(max_length=300, blank=True)
    placed_at    = models.DateTimeField(auto_now_add=True)
    price_at_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                        help_text='Market price at time of bid')

    class Meta:
        ordering = ['-amount', 'placed_at']

    def __str__(self):
        tag = ' [proxy]' if self.is_proxy else ''
        return f"KSh {self.amount:,.0f}{tag} by {self.bidder.name}"


# ── PAYMENT MODELS ─────────────────────────────────────────────────────────────

class MpesaPayment(models.Model):
    """
    Records every M-Pesa STK push initiated and its outcome.
    Paybill: 247247 | Account: 741222
    """
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded',  'Refunded'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('deposit',  'Auction Deposit'),
        ('winning',  'Winning Bid Payment'),
        ('purchase', 'Direct Purchase'),
    ]

    reference        = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment_type     = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)

    # Links — at least one must be set
    auction          = models.ForeignKey(AuctionItem, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='payments')
    bidder           = models.ForeignKey(BidderProfile, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='payments')
    product          = models.ForeignKey(Product, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='payments')

    # M-Pesa fields
    phone_number     = models.CharField(max_length=15, help_text='Payer phone in 254XXXXXXXXX format')
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    vat_amount       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_excl_vat  = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Daraja / STK push fields
    merchant_request_id  = models.CharField(max_length=100, blank=True)
    checkout_request_id  = models.CharField(max_length=100, blank=True, db_index=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, db_index=True)
    transaction_date     = models.CharField(max_length=20, blank=True)

    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_code  = models.CharField(max_length=10, blank=True)
    result_desc  = models.TextField(blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"M-Pesa {self.payment_type} KSh{self.amount} [{self.status}] — {self.phone_number}"

    @property
    def is_paid(self):
        return self.status == 'completed'

    def compute_vat(self):
        """Split amount into excl-VAT and VAT portions. Call before saving."""
        self.amount_excl_vat = (self.amount / (1 + VAT_RATE)).quantize(Decimal('0.01'))
        self.vat_amount      = (self.amount - self.amount_excl_vat).quantize(Decimal('0.01'))

    def generate_invoice_number(self):
        """Human-readable invoice number derived from reference UUID."""
        return f"MNV-{str(self.reference).replace('-','').upper()[:10]}"


class Invoice(models.Model):
    """Generated after a successful payment — PDF-ready data."""
    payment        = models.OneToOneField(MpesaPayment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=30, unique=True)
    issued_at      = models.DateTimeField(auto_now_add=True)
    buyer_name     = models.CharField(max_length=150)
    buyer_phone    = models.CharField(max_length=20)
    buyer_email    = models.EmailField(blank=True)
    subtotal       = models.DecimalField(max_digits=10, decimal_places=2)
    vat_amount     = models.DecimalField(max_digits=10, decimal_places=2)
    total          = models.DecimalField(max_digits=10, decimal_places=2)
    notes          = models.TextField(blank=True)
    pdf_generated  = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice {self.invoice_number} — {self.buyer_name}"


# ── SECURITY EVENT LOG ─────────────────────────────────────────────────────────

class AuctionSecurityEvent(models.Model):
    EVENT_CHOICES = [
        ('rate_limit',     'Rate Limit Hit'),
        ('blocked_bidder', 'Blocked Bidder Attempt'),
        ('duplicate_ip',   'Multiple Phones Same IP'),
        ('invalid_amount', 'Invalid Amount Submitted'),
        ('auction_closed', 'Bid on Closed Auction'),
        ('csrf_fail',      'CSRF Validation Failed'),
        ('proxy_conflict', 'Proxy Bid Conflict'),
    ]
    auction    = models.ForeignKey(AuctionItem, on_delete=models.CASCADE,
                                    related_name='security_events', null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    detail     = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} | {self.ip_address} | {self.created_at:%d %b %H:%M}"
