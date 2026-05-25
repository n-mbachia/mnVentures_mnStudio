from decimal import Decimal
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        # PurchaseLog
        migrations.CreateModel(
            name="PurchaseLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("date",        models.DateField(default=django.utils.timezone.localdate)),
                ("item_name",   models.CharField(max_length=200)),
                ("category",    models.CharField(max_length=30, default="raw_material", choices=[("raw_material","Raw Materials"),("packaging","Packaging"),("consumable","Consumables / Sundries"),("hardware","Hardware & Fittings"),("timber","Timber & Board"),("finishing","Finishing Products (Paint, Lacquer, Oil)"),("adhesive","Adhesives & Sealants"),("tool","Tools & Equipment"),("safety","Safety & PPE"),("other","Other")])),
                ("quantity",    models.DecimalField(max_digits=12, decimal_places=3, validators=[django.core.validators.MinValueValidator(Decimal("0.001"))])),
                ("unit",        models.CharField(max_length=10, default="pcs")),
                ("unit_cost",   models.DecimalField(max_digits=12, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("total_cost",  models.DecimalField(max_digits=14, decimal_places=2, editable=False, default=Decimal("0.00"))),
                ("supplier",    models.CharField(max_length=150, blank=True)),
                ("receipt_ref", models.CharField(max_length=100, blank=True)),
                ("notes",       models.TextField(blank=True)),
                ("created_at",  models.DateTimeField(auto_now_add=True)),
                ("updated_at",  models.DateTimeField(auto_now=True)),
            ],
            options={"ordering":["-date","-created_at"],"verbose_name":"Purchase","verbose_name_plural":"Purchase Log"},
        ),
        # ExpenseLog
        migrations.CreateModel(
            name="ExpenseLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("date",           models.DateField(default=django.utils.timezone.localdate)),
                ("description",    models.CharField(max_length=300)),
                ("category",       models.CharField(max_length=20, default="other")),
                ("amount",         models.DecimalField(max_digits=14, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("payment_method", models.CharField(max_length=20, default="mpesa")),
                ("reference",      models.CharField(max_length=100, blank=True)),
                ("notes",          models.TextField(blank=True)),
                ("created_at",     models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering":["-date","-created_at"],"verbose_name":"Expense","verbose_name_plural":"Expense Log"},
        ),
        # MaterialUseLog
        migrations.CreateModel(
            name="MaterialUseLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("date",          models.DateField(default=django.utils.timezone.localdate)),
                ("material_name", models.CharField(max_length=200)),
                ("quantity_used", models.DecimalField(max_digits=12, decimal_places=3, validators=[django.core.validators.MinValueValidator(Decimal("0.001"))])),
                ("unit",          models.CharField(max_length=10, default="pcs")),
                ("unit_cost",     models.DecimalField(max_digits=12, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("line_cost",     models.DecimalField(max_digits=14, decimal_places=2, editable=False, default=Decimal("0.00"))),
                ("source_purchase", models.ForeignKey("compliance.PurchaseLog", on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, related_name="usages")),
                ("job_reference", models.CharField(max_length=100, blank=True)),
                ("notes",         models.TextField(blank=True)),
                ("created_at",    models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering":["-date","-created_at"],"verbose_name":"Material Use","verbose_name_plural":"Material Use Log"},
        ),
        # SalesInvoice
        migrations.CreateModel(
            name="SalesInvoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("date",               models.DateField(default=django.utils.timezone.localdate)),
                ("invoice_number",     models.CharField(max_length=50, unique=True)),
                ("client_name",        models.CharField(max_length=200)),
                ("client_phone",       models.CharField(max_length=30, blank=True)),
                ("description",        models.TextField(blank=True)),
                ("gross_amount",       models.DecimalField(max_digits=14, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("amount_paid",        models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("payment_status",     models.CharField(max_length=20, default="unpaid")),
                ("etims_registered",   models.BooleanField(default=False)),
                ("etims_cu_invoice_no",models.CharField(max_length=100, blank=True)),
                ("notes",              models.TextField(blank=True)),
                ("created_at",         models.DateTimeField(auto_now_add=True)),
                ("updated_at",         models.DateTimeField(auto_now=True)),
            ],
            options={"ordering":["-date","-created_at"],"verbose_name":"Sales Invoice","verbose_name_plural":"Sales Invoices"},
        ),
        # DrawingsLog
        migrations.CreateModel(
            name="DrawingsLog",
            fields=[
                ("id",         models.BigAutoField(auto_created=True, primary_key=True)),
                ("month",      models.PositiveSmallIntegerField()),
                ("year",       models.PositiveSmallIntegerField()),
                ("amount",     models.DecimalField(max_digits=14, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("notes",      models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"unique_together":{("month","year")},"ordering":["-year","-month"],"verbose_name":"Owner Drawings","verbose_name_plural":"Drawings Log"},
        ),
    ]
