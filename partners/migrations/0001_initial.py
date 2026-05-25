from django.db import migrations, models
import django.db.models.deletion
import partners.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PartnerApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name",           models.CharField(max_length=150, verbose_name="Full Name")),
                ("business_name",       models.CharField(max_length=200, verbose_name="Business / Company Name")),
                ("business_type",       models.CharField(choices=[("interior_designer","Interior Designer"),("contractor","Contractor / Builder"),("architect","Architect"),("retailer","Furniture Retailer"),("property_developer","Property Developer"),("other","Other")], max_length=40, verbose_name="Business Type")),
                ("email",               models.EmailField(unique=True, verbose_name="Email Address")),
                ("mobile",              models.CharField(max_length=20, verbose_name="Mobile Number")),
                ("whatsapp",            models.CharField(blank=True, help_text="Leave blank if same as mobile", max_length=20, verbose_name="WhatsApp Number")),
                ("county",              models.CharField(max_length=100, verbose_name="County / Region")),
                ("town",                models.CharField(max_length=100, verbose_name="Town / Estate")),
                ("address_details",     models.TextField(blank=True, verbose_name="Additional Address Details")),
                ("approximate_clients", models.CharField(help_text="e.g. 5–10", max_length=30, verbose_name="Approximate Clients per Month")),
                ("message",             models.TextField(blank=True, verbose_name="Tell us about your business")),
                ("status",              models.CharField(choices=[("pending","Pending Review"),("approved","Approved"),("rejected","Rejected"),("on_hold","On Hold")], default="pending", max_length=20)),
                ("admin_notes",         models.TextField(blank=True, verbose_name="Admin Notes")),
                ("partner_code",        models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name="Partner Code")),
                ("discount_percent",    models.PositiveSmallIntegerField(default=0, verbose_name="Partner Discount (%)")),
                ("submitted_at",        models.DateTimeField(auto_now_add=True)),
                ("reviewed_at",         models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-submitted_at"], "verbose_name": "Partner Application", "verbose_name_plural": "Partner Applications"},
        ),
        migrations.CreateModel(
            name="DesignSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("partner",                   models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="design_submissions", to="partners.partnerapplication", verbose_name="Partner")),
                ("project_title",             models.CharField(max_length=200, verbose_name="Project Title")),
                ("project_type",              models.CharField(choices=[("cabinet","Cabinet / Joinery"),("furniture","Custom Furniture"),("construction","Construction / Interior Fit-out"),("office","Office Fit-out"),("kitchen","Kitchen Design"),("bedroom","Bedroom & Wardrobes"),("other","Other")], max_length=30, verbose_name="Project Type")),
                ("description",               models.TextField(verbose_name="Project Description")),
                ("site_location",             models.CharField(max_length=200, verbose_name="Project / Site Location")),
                ("expected_start_date",       models.DateField(verbose_name="Expected Start Date")),
                ("expected_completion_date",  models.DateField(verbose_name="Expected Completion Date")),
                ("priority",                  models.CharField(choices=[("standard","Standard"),("urgent","Urgent (within 2 weeks)"),("flexible","Flexible / No rush")], default="standard", max_length=20, verbose_name="Priority Level")),
                ("budget_range",              models.CharField(blank=True, help_text="e.g. 150,000 – 300,000", max_length=100, verbose_name="Approximate Budget (KSh)")),
                ("design_file_1",             models.FileField(blank=True, null=True, upload_to=partners.models.design_upload_path, verbose_name="Design File 1")),
                ("design_file_2",             models.FileField(blank=True, null=True, upload_to=partners.models.design_upload_path, verbose_name="Design File 2")),
                ("design_file_3",             models.FileField(blank=True, null=True, upload_to=partners.models.design_upload_path, verbose_name="Design File 3")),
                ("workshop_status",           models.CharField(choices=[("submitted","Submitted"),("reviewing","Under Review"),("quoted","Quote Sent"),("in_progress","In Progress"),("completed","Completed"),("cancelled","Cancelled")], default="submitted", max_length=20, verbose_name="Workshop Status")),
                ("admin_notes",               models.TextField(blank=True, verbose_name="Admin / Workshop Notes")),
                ("quoted_amount",             models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Quoted Amount (KSh)")),
                ("assigned_to",               models.CharField(blank=True, max_length=100, verbose_name="Assigned to (Workshop Staff)")),
                ("submitted_at",              models.DateTimeField(auto_now_add=True)),
                ("updated_at",                models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-submitted_at"], "verbose_name": "Design Submission", "verbose_name_plural": "Design Submissions"},
        ),
    ]
