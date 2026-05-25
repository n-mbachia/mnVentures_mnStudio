from django.db import models
from django.utils import timezone


# ─── Partner Application ────────────────────────────────────────────────────

class PartnerApplication(models.Model):

    STATUS_CHOICES = [
        ("pending",  "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("on_hold",  "On Hold"),
    ]

    BUSINESS_TYPE_CHOICES = [
        ("interior_designer", "Interior Designer"),
        ("contractor",        "Contractor / Builder"),
        ("architect",         "Architect"),
        ("retailer",          "Furniture Retailer"),
        ("property_developer","Property Developer"),
        ("other",             "Other"),
    ]

    # ── Contact details ──────────────────────────────────────────────────────
    full_name       = models.CharField(max_length=150, verbose_name="Full Name")
    business_name   = models.CharField(max_length=200, verbose_name="Business / Company Name")
    business_type   = models.CharField(
        max_length=40, choices=BUSINESS_TYPE_CHOICES, verbose_name="Business Type"
    )
    email           = models.EmailField(unique=True, verbose_name="Email Address")
    mobile          = models.CharField(max_length=20,  verbose_name="Mobile Number")
    whatsapp        = models.CharField(
        max_length=20, blank=True,
        verbose_name="WhatsApp Number",
        help_text="Leave blank if same as mobile"
    )

    # ── Location ─────────────────────────────────────────────────────────────
    county          = models.CharField(max_length=100, verbose_name="County / Region")
    town            = models.CharField(max_length=100, verbose_name="Town / Estate")
    address_details = models.TextField(
        blank=True, verbose_name="Additional Address Details",
        help_text="Building name, road, landmarks etc."
    )

    # ── Business context ─────────────────────────────────────────────────────
    approximate_clients = models.CharField(
        max_length=30, verbose_name="Approximate Clients per Month",
        help_text="e.g. 5–10"
    )
    message         = models.TextField(
        blank=True, verbose_name="Tell us about your business",
        help_text="What type of projects do you work on?"
    )

    # ── Admin workflow ────────────────────────────────────────────────────────
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    admin_notes     = models.TextField(blank=True, verbose_name="Admin Notes")
    partner_code    = models.CharField(
        max_length=20, blank=True, unique=True, null=True,
        verbose_name="Partner Code",
        help_text="Auto-generated when application is approved"
    )
    discount_percent= models.PositiveSmallIntegerField(
        default=0, verbose_name="Partner Discount (%)",
        help_text="Special pricing discount awarded to this partner"
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    submitted_at    = models.DateTimeField(auto_now_add=True)
    reviewed_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Partner Application"
        verbose_name_plural = "Partner Applications"

    def __str__(self):
        return f"{self.business_name} ({self.full_name}) — {self.get_status_display()}"

    def approve(self, discount=10):
        """Approve the partner and generate a partner code."""
        import random, string
        self.status = "approved"
        self.discount_percent = discount
        self.reviewed_at = timezone.now()
        if not self.partner_code:
            prefix = self.business_name[:3].upper()
            suffix = "".join(random.choices(string.digits, k=5))
            self.partner_code = f"MNV-{prefix}-{suffix}"
        self.save()


# ─── Design / Project Submission ────────────────────────────────────────────

def design_upload_path(instance, filename):
    return f"partner_designs/{instance.partner.id}/{filename}"


class DesignSubmission(models.Model):

    PROJECT_TYPE_CHOICES = [
        ("cabinet",      "Cabinet / Joinery"),
        ("furniture",    "Custom Furniture"),
        ("construction", "Construction / Interior Fit-out"),
        ("office",       "Office Fit-out"),
        ("kitchen",      "Kitchen Design"),
        ("bedroom",      "Bedroom & Wardrobes"),
        ("other",        "Other"),
    ]

    PRIORITY_CHOICES = [
        ("standard", "Standard"),
        ("urgent",   "Urgent (within 2 weeks)"),
        ("flexible", "Flexible / No rush"),
    ]

    WORKSHOP_STATUS_CHOICES = [
        ("submitted",  "Submitted"),
        ("reviewing",  "Under Review"),
        ("quoted",     "Quote Sent"),
        ("in_progress","In Progress"),
        ("completed",  "Completed"),
        ("cancelled",  "Cancelled"),
    ]

    # ── Relationship ─────────────────────────────────────────────────────────
    partner         = models.ForeignKey(
        PartnerApplication, on_delete=models.CASCADE,
        related_name="design_submissions",
        verbose_name="Partner"
    )

    # ── Project info ──────────────────────────────────────────────────────────
    project_title   = models.CharField(max_length=200, verbose_name="Project Title")
    project_type    = models.CharField(
        max_length=30, choices=PROJECT_TYPE_CHOICES, verbose_name="Project Type"
    )
    description     = models.TextField(verbose_name="Project Description")
    site_location   = models.CharField(
        max_length=200, verbose_name="Project / Site Location"
    )

    # ── Timeline ─────────────────────────────────────────────────────────────
    expected_start_date     = models.DateField(
        verbose_name="Expected Start Date"
    )
    expected_completion_date= models.DateField(
        verbose_name="Expected Completion Date"
    )
    priority        = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="standard",
        verbose_name="Priority Level"
    )

    # ── Budget ────────────────────────────────────────────────────────────────
    budget_range    = models.CharField(
        max_length=100, blank=True,
        verbose_name="Approximate Budget (KSh)",
        help_text="e.g. 150,000 – 300,000"
    )

    # ── Files ─────────────────────────────────────────────────────────────────
    design_file_1   = models.FileField(
        upload_to=design_upload_path, blank=True, null=True,
        verbose_name="Design File 1",
        help_text="PDF, DWG, JPG, PNG (max 20 MB)"
    )
    design_file_2   = models.FileField(
        upload_to=design_upload_path, blank=True, null=True,
        verbose_name="Design File 2"
    )
    design_file_3   = models.FileField(
        upload_to=design_upload_path, blank=True, null=True,
        verbose_name="Design File 3"
    )

    # ── Admin / Workshop workflow ─────────────────────────────────────────────
    workshop_status = models.CharField(
        max_length=20, choices=WORKSHOP_STATUS_CHOICES, default="submitted",
        verbose_name="Workshop Status"
    )
    admin_notes     = models.TextField(blank=True, verbose_name="Admin / Workshop Notes")
    quoted_amount   = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Quoted Amount (KSh)"
    )
    assigned_to     = models.CharField(
        max_length=100, blank=True, verbose_name="Assigned to (Workshop Staff)"
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    submitted_at    = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Design Submission"
        verbose_name_plural = "Design Submissions"

    def __str__(self):
        return f"{self.project_title} — {self.partner.business_name}"

    @property
    def file_list(self):
        """Return a list of (label, file) for all uploaded design files."""
        files = []
        for i in range(1, 4):
            f = getattr(self, f"design_file_{i}")
            if f:
                files.append((f"Design {i}", f))
        return files
