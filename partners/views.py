from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q

from .models import PartnerApplication, DesignSubmission
from .forms import PartnerApplicationForm, DesignSubmissionForm


# ─── Public: Partner registration ───────────────────────────────────────────

def become_partner(request):
    """Landing + registration form for new partner applications."""
    if request.method == "POST":
        form = PartnerApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            request.session["partner_application_id"] = application.pk
            messages.success(
                request,
                "Thank you! Your application has been received. "
                "We will review it and contact you within 2 business days."
            )
            return redirect("partners:apply_success")
    else:
        form = PartnerApplicationForm()

    return render(request, "partners/become_partner.html", {"form": form})


def apply_success(request):
    return render(request, "partners/apply_success.html")


# ─── Public: Design submission (for approved partners) ───────────────────────

def submit_design(request):
    """
    Partners submit designs / project briefs.
    We ask for their email to look up their approved application.
    """
    partner = None
    email   = request.GET.get("email") or request.POST.get("partner_email", "")

    if email:
        try:
            partner = PartnerApplication.objects.get(email=email, status="approved")
        except PartnerApplication.DoesNotExist:
            messages.error(
                request,
                "No approved partner account was found for that email address. "
                "Please apply first or contact us on WhatsApp."
            )

    if request.method == "POST" and partner:
        form = DesignSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.partner = partner
            submission.save()
            messages.success(
                request,
                f"Design submitted successfully! "
                f"Reference: #{submission.pk:05d}. "
                "Our team will review and get back to you shortly."
            )
            return redirect("partners:submit_success")
    else:
        form = DesignSubmissionForm()

    return render(request, "partners/submit_design.html", {
        "form":    form,
        "partner": partner,
        "email":   email,
    })


def submit_success(request):
    return render(request, "partners/submit_success.html")


# ─── Staff: Admin dashboard ──────────────────────────────────────────────────

@staff_member_required
def admin_dashboard(request):
    """Overview dashboard for all partner applications and design submissions."""
    q = request.GET.get("q", "")

    applications = PartnerApplication.objects.all()
    if q:
        applications = applications.filter(
            Q(full_name__icontains=q) |
            Q(business_name__icontains=q) |
            Q(email__icontains=q) |
            Q(county__icontains=q)
        )

    submissions = DesignSubmission.objects.select_related("partner").all()
    if q:
        submissions = submissions.filter(
            Q(project_title__icontains=q) |
            Q(partner__business_name__icontains=q) |
            Q(site_location__icontains=q)
        )

    context = {
        "applications":   applications,
        "submissions":    submissions,
        "q":              q,
        "pending_count":  PartnerApplication.objects.filter(status="pending").count(),
        "approved_count": PartnerApplication.objects.filter(status="approved").count(),
        "open_jobs":      DesignSubmission.objects.exclude(
            workshop_status__in=["completed", "cancelled"]
        ).count(),
    }
    return render(request, "partners/admin_dashboard.html", context)


@staff_member_required
def admin_application_detail(request, pk):
    """Detail + status-change view for a single partner application."""
    application = get_object_or_404(PartnerApplication, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            discount = int(request.POST.get("discount", 10))
            application.approve(discount=discount)
            messages.success(request, f"Partner approved. Code: {application.partner_code}")
        elif action == "reject":
            application.status    = "rejected"
            application.reviewed_at = timezone.now()
            application.save()
            messages.warning(request, "Application rejected.")
        elif action == "on_hold":
            application.status    = "on_hold"
            application.reviewed_at = timezone.now()
            application.save()
            messages.info(request, "Application placed on hold.")
        application.admin_notes = request.POST.get("admin_notes", application.admin_notes)
        application.save()
        return redirect("partners:admin_application_detail", pk=pk)

    return render(request, "partners/admin_application_detail.html", {
        "application": application,
        "submissions": application.design_submissions.all(),
    })


@staff_member_required
def admin_submission_detail(request, pk):
    """Detail + workshop-status update for a single design submission."""
    submission = get_object_or_404(DesignSubmission, pk=pk)

    if request.method == "POST":
        submission.workshop_status = request.POST.get("workshop_status", submission.workshop_status)
        submission.admin_notes     = request.POST.get("admin_notes", submission.admin_notes)
        submission.assigned_to     = request.POST.get("assigned_to", submission.assigned_to)
        quoted_raw = request.POST.get("quoted_amount", "")
        if quoted_raw:
            try:
                submission.quoted_amount = float(quoted_raw.replace(",", ""))
            except ValueError:
                pass
        submission.save()
        messages.success(request, "Submission updated successfully.")
        return redirect("partners:admin_submission_detail", pk=pk)

    return render(request, "partners/admin_submission_detail.html", {
        "submission": submission,
    })
