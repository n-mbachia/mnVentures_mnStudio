"""
compliance/models.py
────────────────────────────────────────────────────────────────────────────
MN Ventures — Business Compliance & Analytics
Data layer for purchase tracking, expense logging, material usage, and sales.

All monetary values are stored in Kenya Shillings (KES) as Decimal fields
with two decimal places to preserve precision for statutory calculations.
"""

from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


# ─── Shared choice constants ─────────────────────────────────────────────────

UNIT_CHOICES = [
    # Volume / mass
    ("kg",    "Kilograms (kg)"),
    ("g",     "Grams (g)"),
    ("ltr",   "Litres (ltr)"),
    ("ml",    "Millilitres (ml)"),
    # Length / area
    ("m",     "Metres (m)"),
    ("m2",    "Square Metres (m²)"),
    ("m3",    "Cubic Metres (m³)"),
    ("ft",    "Feet (ft)"),
    # Discrete
    ("pcs",   "Pieces (pcs)"),
    ("sht",   "Sheets"),
    ("set",   "Set"),
    ("roll",  "Roll"),
    ("bag",   "Bag"),
    ("box",   "Box"),
    ("bale",  "Bale"),
    ("lot",   "Lot"),
    ("hr",    "Hours (hr)"),
    ("day",   "Days"),
]

ZERO = Decimal("0.00")


# ─── 1. Purchase Log ─────────────────────────────────────────────────────────

class PurchaseLog(models.Model):
    """
    Records every raw material, supply, or stock purchase.
    `total_cost` is auto-computed on save (quantity × unit_cost).
    """

    CATEGORY_CHOICES = [
        ("raw_material",  "Raw Materials"),
        ("packaging",     "Packaging"),
        ("consumable",    "Consumables / Sundries"),
        ("hardware",      "Hardware & Fittings"),
        ("timber",        "Timber & Board"),
        ("finishing",     "Finishing Products (Paint, Lacquer, Oil)"),
        ("adhesive",      "Adhesives & Sealants"),
        ("tool",          "Tools & Equipment"),
        ("safety",        "Safety & PPE"),
        ("other",         "Other"),
    ]

    date        = models.DateField(default=timezone.localdate, verbose_name="Purchase Date")
    item_name   = models.CharField(max_length=200, verbose_name="Item / Supply Name")
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="raw_material")
    quantity    = models.DecimalField(
        max_digits=12, decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        verbose_name="Quantity"
    )
    unit        = models.CharField(max_length=10, choices=UNIT_CHOICES, default="pcs")
    unit_cost   = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="Unit Cost (KES)"
    )
    total_cost  = models.DecimalField(
        max_digits=14, decimal_places=2,
        editable=False, default=ZERO,
        verbose_name="Total Cost (KES)"
    )
    supplier    = models.CharField(max_length=150, blank=True, verbose_name="Supplier Name")
    receipt_ref = models.CharField(max_length=100, blank=True, verbose_name="Receipt / LPO Reference")
    notes       = models.TextField(blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Purchase"
        verbose_name_plural = "Purchase Log"

    def save(self, *args, **kwargs):
        self.total_cost = (self.quantity * self.unit_cost).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} | {self.item_name} — KES {self.total_cost:,.2f}"


# ─── 2. Expense Log ──────────────────────────────────────────────────────────

class ExpenseLog(models.Model):
    """
    Operational expense entries — everything that is NOT a material purchase
    or a statutory payment (those are computed separately).
    """

    CATEGORY_CHOICES = [
        ("transport",    "Transport & Delivery"),
        ("utilities",    "Utilities (Power, Water, Internet)"),
        ("rent",         "Rent / Premises"),
        ("wages",        "Casual Wages / Labour"),
        ("marketing",    "Marketing & Advertising"),
        ("maintenance",  "Maintenance & Repairs"),
        ("professional", "Professional Services (Accountant, Legal)"),
        ("consumable",   "Consumables / Office"),
        ("fuel",         "Fuel & Vehicle"),
        ("bank",         "Bank Charges & Mobile Money"),
        ("other",        "Other"),
    ]

    date        = models.DateField(default=timezone.localdate, verbose_name="Date")
    description = models.CharField(max_length=300, verbose_name="Expense Description")
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    amount      = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="Amount (KES)"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ("cash",   "Cash"),
            ("mpesa",  "M-Pesa"),
            ("bank",   "Bank Transfer"),
            ("card",   "Card"),
            ("other",  "Other"),
        ],
        default="mpesa"
    )
    reference   = models.CharField(max_length=100, blank=True, verbose_name="Reference / Receipt No.")
    notes       = models.TextField(blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Expense"
        verbose_name_plural = "Expense Log"

    def __str__(self):
        return f"{self.date} | {self.description} — KES {self.amount:,.2f}"


# ─── 3. Material Use Log ─────────────────────────────────────────────────────

class MaterialUseLog(models.Model):
    """
    Records materials consumed in production for a specific job or batch.
    `unit_cost` is manually entered (reflecting the most recent purchase price)
    or can be linked to a PurchaseLog entry for FIFO/weighted-average valuation.
    `line_cost` (qty × unit_cost) feeds directly into COGS computation.
    """

    date         = models.DateField(default=timezone.localdate, verbose_name="Date Used")
    material_name= models.CharField(max_length=200, verbose_name="Material Name")
    quantity_used= models.DecimalField(
        max_digits=12, decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        verbose_name="Quantity Used"
    )
    unit         = models.CharField(max_length=10, choices=UNIT_CHOICES, default="pcs")
    unit_cost    = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="Unit Cost at Use (KES)",
        help_text="Cost per unit at the time of use — reference historical purchase price"
    )
    line_cost    = models.DecimalField(
        max_digits=14, decimal_places=2,
        editable=False, default=ZERO,
        verbose_name="Line Cost (KES)"
    )

    # Optional reference back to the source purchase for traceability
    source_purchase = models.ForeignKey(
        PurchaseLog, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="usages",
        verbose_name="Source Purchase (optional)"
    )

    job_reference= models.CharField(
        max_length=100, blank=True,
        verbose_name="Job / Batch Reference",
        help_text="e.g. JC-0042 or Production Batch #7"
    )
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Material Use"
        verbose_name_plural = "Material Use Log"

    def save(self, *args, **kwargs):
        self.line_cost = (self.quantity_used * self.unit_cost).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} | {self.material_name} × {self.quantity_used} {self.unit} — KES {self.line_cost:,.2f}"


# ─── 4. Sales Invoice ────────────────────────────────────────────────────────

class SalesInvoice(models.Model):
    """
    Records every sales transaction.  Gross sales feed into TOT, Gross Profit,
    and Net Profit calculations.  eTIMS compliance flag is tracked per invoice.
    """

    PAYMENT_STATUS_CHOICES = [
        ("unpaid",       "Unpaid"),
        ("partial",      "Partially Paid"),
        ("paid",         "Fully Paid"),
        ("overdue",      "Overdue"),
        ("cancelled",    "Cancelled / Reversed"),
    ]

    date            = models.DateField(default=timezone.localdate, verbose_name="Invoice Date")
    invoice_number = models.CharField(
        max_length=50, 
        unique=True,
        blank=True,  # Allows the field to be left empty in forms
        verbose_name="Invoice Number",
        help_text="Automatically generated (e.g., MN-05-26-2026-00001)"
    )

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # 1. Get current date parts
            today_dt = timezone.now()
            month_str = today_dt.strftime('%m')   # "05"
            day_str = today_dt.strftime('%d')     # "26"
            year_str = today_dt.strftime('%Y')    # "2026"
            
            # 2. Define the prefix string for today
            prefix = f"MNV-{month_str}-{day_str}-{year_str}-"
            
            # 3. Find the last invoice created today with this prefix
            last_invoice = SalesInvoice.objects.filter(
                invoice_number__startswith=prefix
            ).order_by('invoice_number').last()
            
            if last_invoice:
                # Extract the number part from the end, convert to integer, and increment
                try:
                    last_sequence = int(last_invoice.invoice_number.split('-')[-1])
                    next_sequence = last_sequence + 1
                except (ValueError, IndexErrors):
                    next_sequence = 1
            else:
                # First invoice of the day
                next_sequence = 1
            
            # 4. Format string with padding zero-fills up to 5 digits
            self.invoice_number = f"{prefix}{next_sequence:05d}"
            
        super().save(*args, **kwargs)
    client_name     = models.CharField(max_length=200, verbose_name="Client / Buyer Name")
    client_phone    = models.CharField(max_length=30,  blank=True, verbose_name="Client Phone")
    description     = models.TextField(
        blank=True, verbose_name="Description of Goods / Services",
        help_text="Summary of what was sold"
    )

    # ── Financials ────────────────────────────────────────────────────────────
    gross_amount    = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="Gross Sales Amount (KES)",
        help_text="Total revenue collected before any deductions"
    )
    amount_paid     = models.DecimalField(
        max_digits=14, decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
        verbose_name="Amount Paid (KES)"
    )
    payment_status  = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="unpaid"
    )

    # ── eTIMS compliance ──────────────────────────────────────────────────────
    etims_registered = models.BooleanField(
        default=False,
        verbose_name="eTIMS Invoice Raised",
        help_text="Has this transaction been recorded in the KRA eTIMS system?"
    )
    etims_cu_invoice_no = models.CharField(
        max_length=100, blank=True,
        verbose_name="eTIMS CU Invoice Number",
        help_text="Control Unit invoice number from KRA eTIMS portal"
    )

    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Sales Invoice"
        verbose_name_plural = "Sales Invoices"

    def __str__(self):
        return f"{self.invoice_number} | {self.client_name} — KES {self.gross_amount:,.2f}"

    @property
    def balance_due(self):
        return max(self.gross_amount - self.amount_paid, ZERO)


# ─── 5. Drawings Log (owner's personal income draw) ─────────────────────────

class DrawingsLog(models.Model):
    """
    Tracks the owner's personal drawings from the business.
    Used as the base for AHL (Affordable Housing Levy) computation
    when the owner prefers to use actual drawings rather than net profit.
    """

    month       = models.PositiveSmallIntegerField(verbose_name="Month (1–12)")
    year        = models.PositiveSmallIntegerField(verbose_name="Year")
    amount      = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        verbose_name="Drawings Amount (KES)"
    )
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("month", "year")]
        ordering = ["-year", "-month"]
        verbose_name = "Owner Drawings"
        verbose_name_plural = "Drawings Log"

    def __str__(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year} — KES {self.amount:,.2f}"
