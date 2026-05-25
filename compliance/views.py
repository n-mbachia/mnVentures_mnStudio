"""
compliance/views.py
────────────────────────────────────────────────────────────────────────────
Views:
  dashboard          — main P&L + statutory dashboard
  sales_portal       — dedicated sales invoice management (list + add + edit)
  sales_edit         — edit / eTIMS-toggle on an existing invoice
  sales_delete       — delete a sales invoice
  add_purchase       — quick-add POST
  add_expense        — quick-add POST
  add_material_use   — quick-add POST
  add_drawings       — quick-add POST (no longer a hidden-panel add_invoice)
"""

import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import (
    PeriodSelectForm, PurchaseForm, ExpenseForm,
    MaterialUseForm, SalesInvoiceForm, DrawingsForm,
)
from .models import PurchaseLog, ExpenseLog, MaterialUseLog, SalesInvoice, DrawingsLog
from .services import build_dashboard_context


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_decimal(value, default="0"):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def _redirect_dashboard(month=None, year=None):
    """Redirect back to dashboard preserving the current period."""
    url = reverse("compliance:dashboard")
    if month and year:
        url += f"?month={month}&year={year}"
    return redirect(url)


# ─── Main dashboard ───────────────────────────────────────────────────────────

@staff_member_required
def dashboard(request):
    today = datetime.date.today()
    month = int(request.GET.get("month", today.month))
    year  = int(request.GET.get("year",  today.year))
    nssf  = _safe_decimal(request.GET.get("nssf", "0"))
    use_drawings = request.GET.get("use_drawings") == "on"

    # Bind the period form from GET if the user submitted it, else use initial
    if any(k in request.GET for k in ("month", "year", "nssf", "use_drawings")):
        period_form = PeriodSelectForm(request.GET)
    else:
        period_form = PeriodSelectForm(
            initial={"month": month, "year": year, "nssf": "0", "use_drawings": False}
        )

    ctx = build_dashboard_context(
        month=month, year=year,
        nssf_contribution=nssf,
        use_drawings_override=use_drawings,
    )
    ctx["period_form"] = period_form

    # Recent entries for sidebar panels
    ctx["recent_purchases"] = PurchaseLog.objects.all()[:6]
    ctx["recent_expenses"]  = ExpenseLog.objects.all()[:6]
    ctx["recent_materials"] = MaterialUseLog.objects.all()[:6]
    ctx["recent_invoices"]  = SalesInvoice.objects.filter(
        date__year=year, date__month=month
    ).order_by("-date")[:8]

    # Quick-add forms (purchase / expense / material only;
    # sales now has its own dedicated portal)
    ctx["purchase_form"]  = PurchaseForm()
    ctx["expense_form"]   = ExpenseForm()
    ctx["material_form"]  = MaterialUseForm()
    ctx["drawings_form"]  = DrawingsForm()

    return render(request, "compliance/dashboard.html", ctx)


# ─── Sales portal (dedicated page) ───────────────────────────────────────────

@staff_member_required
def sales_portal(request):
    """
    Full sales management page:
    • Lists all invoices (with optional month/year filter)
    • Inline Add form at the top
    • Per-row eTIMS toggle and payment-status update
    • Running totals for the filtered period
    """
    today = datetime.date.today()
    month = request.GET.get("month", "")
    year  = request.GET.get("year", str(today.year))

    invoices = SalesInvoice.objects.all().order_by("-date", "-created_at")
    if month:
        invoices = invoices.filter(date__month=int(month), date__year=int(year))
    elif year:
        invoices = invoices.filter(date__year=int(year))

    # Aggregates for the filtered set
    totals = invoices.aggregate(
        total_invoiced=Sum("gross_amount"),
        total_paid=Sum("amount_paid"),
    )
    total_invoiced  = _safe_decimal(totals["total_invoiced"])
    total_paid      = _safe_decimal(totals["total_paid"])
    total_outstanding = max(total_invoiced - total_paid, Decimal("0"))
    etims_ok  = invoices.filter(etims_registered=True).count()
    etims_bad = invoices.filter(etims_registered=False).count()

    # Handle the Add form POST
    add_form = SalesInvoiceForm()
    if request.method == "POST" and request.POST.get("_action") == "add":
        add_form = SalesInvoiceForm(request.POST)
        if add_form.is_valid():
            add_form.save()
            messages.success(request, "Invoice recorded successfully ✓")
            return redirect(reverse("compliance:sales_portal") + f"?year={year}&month={month}")
        else:
            messages.error(request, "Please correct the errors below.")

    # Month choices for the filter selector
    import calendar
    month_choices = [("", "All months")] + [(str(i), calendar.month_name[i]) for i in range(1, 13)]
    year_choices  = [str(y) for y in range(2024, 2031)]

    ctx = {
        "invoices":          invoices,
        "add_form":          add_form,
        "month":             month,
        "year":              year,
        "month_choices":     month_choices,
        "year_choices":      year_choices,
        "total_invoiced":    total_invoiced,
        "total_paid":        total_paid,
        "total_outstanding": total_outstanding,
        "etims_ok":          etims_ok,
        "etims_bad":         etims_bad,
        "invoice_count":     invoices.count(),
    }
    return render(request, "compliance/sales.html", ctx)


@staff_member_required
def sales_edit(request, pk):
    """Edit an existing sales invoice (full form)."""
    invoice = get_object_or_404(SalesInvoice, pk=pk)

    if request.method == "POST":
        form = SalesInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, f"Invoice {invoice.invoice_number} updated ✓")
            return redirect(reverse("compliance:sales_portal"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SalesInvoiceForm(instance=invoice)

    return render(request, "compliance/sales_edit.html", {
        "form":    form,
        "invoice": invoice,
    })


@staff_member_required
def sales_delete(request, pk):
    """Delete a sales invoice (POST only)."""
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    if request.method == "POST":
        ref = invoice.invoice_number
        invoice.delete()
        messages.success(request, f"Invoice {ref} deleted.")
    return redirect(reverse("compliance:sales_portal"))


@staff_member_required
def sales_toggle_etims(request, pk):
    """Toggle eTIMS registration flag on an invoice (POST only)."""
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    if request.method == "POST":
        invoice.etims_registered = not invoice.etims_registered
        if invoice.etims_registered:
            cu_no = request.POST.get("etims_cu_invoice_no", "").strip()
            if cu_no:
                invoice.etims_cu_invoice_no = cu_no
        invoice.save()
        status = "registered on eTIMS ✓" if invoice.etims_registered else "removed from eTIMS"
        messages.success(request, f"{invoice.invoice_number} {status}")
    return redirect(request.META.get("HTTP_REFERER", reverse("compliance:sales_portal")))


@staff_member_required
def sales_update_payment(request, pk):
    """Update payment status and amount paid (POST only)."""
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    if request.method == "POST":
        invoice.payment_status = request.POST.get("payment_status", invoice.payment_status)
        paid_raw = request.POST.get("amount_paid", "")
        if paid_raw:
            invoice.amount_paid = _safe_decimal(paid_raw, str(invoice.amount_paid))
        invoice.save()
        messages.success(request, f"Payment updated for {invoice.invoice_number} ✓")
    return redirect(request.META.get("HTTP_REFERER", reverse("compliance:sales_portal")))


# ─── Quick-add POST handlers (dashboard panels) ───────────────────────────────

def _post_quick_add(request, form_class, success_msg):
    """
    Generic handler for quick-add forms.
    On success: redirects back to dashboard (preserving month/year).
    On error:   redirects back with a Django message containing field errors.
    """
    if request.method != "POST":
        return _redirect_dashboard()

    form = form_class(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, success_msg)
    else:
        # Collect field errors into a readable string
        error_text = "; ".join(
            f"{field}: {', '.join(errs)}"
            for field, errs in form.errors.items()
        )
        messages.error(request, f"Could not save — {error_text}")

    # Redirect back to wherever the user was (dashboard with period params)
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return _redirect_dashboard(
        month=request.POST.get("_month"),
        year=request.POST.get("_year"),
    )


@staff_member_required
def add_purchase(request):
    return _post_quick_add(request, PurchaseForm, "Purchase recorded ✓")


@staff_member_required
def add_expense(request):
    return _post_quick_add(request, ExpenseForm, "Expense recorded ✓")


@staff_member_required
def add_material_use(request):
    return _post_quick_add(request, MaterialUseForm, "Material use recorded ✓")


@staff_member_required
def add_drawings(request):
    return _post_quick_add(request, DrawingsForm, "Owner drawings recorded ✓")
