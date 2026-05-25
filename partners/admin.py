from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import PartnerApplication, DesignSubmission


class DesignSubmissionInline(admin.TabularInline):
    model  = DesignSubmission
    extra  = 0
    fields = ("project_title", "project_type", "workshop_status", "submitted_at")
    readonly_fields = ("submitted_at",)
    show_change_link = True


@admin.register(PartnerApplication)
class PartnerApplicationAdmin(admin.ModelAdmin):
    list_display  = (
        "business_name", "full_name", "county", "mobile",
        "status_badge", "partner_code", "discount_percent", "submitted_at"
    )
    list_filter   = ("status", "business_type", "county")
    search_fields = ("full_name", "business_name", "email", "mobile", "partner_code")
    readonly_fields = ("submitted_at", "reviewed_at", "partner_code")
    inlines       = [DesignSubmissionInline]

    fieldsets = (
        ("Contact Details", {
            "fields": ("full_name", "business_name", "business_type", "email", "mobile", "whatsapp")
        }),
        ("Location", {
            "fields": ("county", "town", "address_details")
        }),
        ("Business Context", {
            "fields": ("approximate_clients", "message")
        }),
        ("Admin & Partner Settings", {
            "fields": ("status", "admin_notes", "partner_code", "discount_percent", "reviewed_at")
        }),
        ("Timestamps", {
            "fields": ("submitted_at",),
            "classes": ("collapse",)
        }),
    )

    actions = ["approve_selected", "reject_selected"]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colours = {
            "pending":  "#f59e0b",
            "approved": "#10b981",
            "rejected": "#ef4444",
            "on_hold":  "#6b7280",
        }
        colour = colours.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            colour, obj.get_status_display()
        )

    @admin.action(description="Approve selected applications (10%% discount)")
    def approve_selected(self, request, queryset):
        for app in queryset.filter(status="pending"):
            app.approve(discount=10)
        self.message_user(request, f"Approved {queryset.filter(status='approved').count()} applications.")

    @admin.action(description="Reject selected applications")
    def reject_selected(self, request, queryset):
        from django.utils import timezone
        queryset.update(status="rejected", reviewed_at=timezone.now())


@admin.register(DesignSubmission)
class DesignSubmissionAdmin(admin.ModelAdmin):
    list_display  = (
        "project_title", "partner_link", "project_type",
        "priority", "workshop_status_badge", "submitted_at"
    )
    list_filter   = ("workshop_status", "project_type", "priority")
    search_fields = ("project_title", "partner__business_name", "site_location")
    readonly_fields = ("submitted_at", "updated_at")

    fieldsets = (
        ("Project Details", {
            "fields": ("partner", "project_title", "project_type", "description", "site_location")
        }),
        ("Timeline & Budget", {
            "fields": ("expected_start_date", "expected_completion_date", "priority", "budget_range")
        }),
        ("Design Files", {
            "fields": ("design_file_1", "design_file_2", "design_file_3")
        }),
        ("Workshop Workflow", {
            "fields": ("workshop_status", "admin_notes", "quoted_amount", "assigned_to")
        }),
        ("Timestamps", {
            "fields": ("submitted_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Partner")
    def partner_link(self, obj):
        url = reverse("admin:partners_partnerapplication_change", args=[obj.partner.pk])
        return format_html('<a href="{}">{}</a>', url, obj.partner.business_name)

    @admin.display(description="Workshop Status")
    def workshop_status_badge(self, obj):
        colours = {
            "submitted":   "#6b7280",
            "reviewing":   "#3b82f6",
            "quoted":      "#f59e0b",
            "in_progress": "#8b5cf6",
            "completed":   "#10b981",
            "cancelled":   "#ef4444",
        }
        colour = colours.get(obj.workshop_status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            colour, obj.get_workshop_status_display()
        )
