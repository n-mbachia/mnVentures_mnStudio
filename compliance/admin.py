"""compliance/admin.py"""
from django.contrib import admin
from django.utils.html import format_html
from .models import PurchaseLog, ExpenseLog, MaterialUseLog, SalesInvoice, DrawingsLog


@admin.register(PurchaseLog)
class PurchaseAdmin(admin.ModelAdmin):
    list_display  = ("date","item_name","category","quantity","unit","unit_cost","total_cost","supplier")
    list_filter   = ("category","date")
    search_fields = ("item_name","supplier","receipt_ref")
    readonly_fields = ("total_cost","created_at","updated_at")
    date_hierarchy  = "date"


@admin.register(ExpenseLog)
class ExpenseAdmin(admin.ModelAdmin):
    list_display  = ("date","description","category","amount","payment_method","reference")
    list_filter   = ("category","payment_method","date")
    search_fields = ("description","reference")
    date_hierarchy = "date"


@admin.register(MaterialUseLog)
class MaterialUseAdmin(admin.ModelAdmin):
    list_display  = ("date","material_name","quantity_used","unit","unit_cost","line_cost","job_reference")
    list_filter   = ("unit","date")
    search_fields = ("material_name","job_reference")
    readonly_fields = ("line_cost","created_at")
    date_hierarchy  = "date"


@admin.register(SalesInvoice)
class SalesInvoiceAdmin(admin.ModelAdmin):
    list_display  = ("date","invoice_number","client_name","gross_amount","payment_status","etims_badge")
    list_filter   = ("payment_status","etims_registered","date")
    search_fields = ("invoice_number","client_name","etims_cu_invoice_no")
    readonly_fields = ("created_at","updated_at")
    date_hierarchy  = "date"

    @admin.display(description="eTIMS")
    def etims_badge(self, obj):
        if obj.etims_registered:
            return format_html('<span style="color:#059669;font-weight:700">✓ Raised</span>')
        return format_html('<span style="color:#dc2626;font-weight:700">✗ Pending</span>')


@admin.register(DrawingsLog)
class DrawingsAdmin(admin.ModelAdmin):
    list_display = ("year","month","amount","notes")
    list_filter  = ("year",)
