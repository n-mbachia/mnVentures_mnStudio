"""
compliance/forms.py  ── quick-entry forms for all four log models
"""
from django import forms
from .models import PurchaseLog, ExpenseLog, MaterialUseLog, SalesInvoice, DrawingsLog

_cls = "block w-full rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-400"


def _w(widget_class, **attrs):
    attrs.setdefault("class", _cls)
    return widget_class(attrs=attrs)


class PurchaseForm(forms.ModelForm):
    class Meta:
        model  = PurchaseLog
        fields = ["date","item_name","category","quantity","unit","unit_cost","supplier","receipt_ref","notes"]
        widgets = {
            "date":        _w(forms.DateInput, type="date"),
            "item_name":   _w(forms.TextInput,  placeholder="e.g. 18mm MDF Board"),
            "category":    _w(forms.Select),
            "quantity":    _w(forms.NumberInput, step="0.001", min="0"),
            "unit":        _w(forms.Select),
            "unit_cost":   _w(forms.NumberInput, step="0.01",  min="0"),
            "supplier":    _w(forms.TextInput,   placeholder="e.g. Gikomba Timber"),
            "receipt_ref": _w(forms.TextInput,   placeholder="Receipt / LPO number"),
            "notes":       _w(forms.Textarea,    rows="2"),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model  = ExpenseLog
        fields = ["date","description","category","amount","payment_method","reference","notes"]
        widgets = {
            "date":           _w(forms.DateInput,  type="date"),
            "description":    _w(forms.TextInput,  placeholder="e.g. Electricity Bill – April"),
            "category":       _w(forms.Select),
            "amount":         _w(forms.NumberInput, step="0.01", min="0"),
            "payment_method": _w(forms.Select),
            "reference":      _w(forms.TextInput,  placeholder="M-Pesa ref / Receipt"),
            "notes":          _w(forms.Textarea,   rows="2"),
        }


class MaterialUseForm(forms.ModelForm):
    class Meta:
        model  = MaterialUseLog
        fields = ["date","material_name","quantity_used","unit","unit_cost","source_purchase","job_reference","notes"]
        widgets = {
            "date":           _w(forms.DateInput,  type="date"),
            "material_name":  _w(forms.TextInput,  placeholder="e.g. Mahogany A-grade"),
            "quantity_used":  _w(forms.NumberInput, step="0.001", min="0"),
            "unit":           _w(forms.Select),
            "unit_cost":      _w(forms.NumberInput, step="0.01",  min="0"),
            "source_purchase":_w(forms.Select),
            "job_reference":  _w(forms.TextInput,  placeholder="e.g. JC-0042"),
            "notes":          _w(forms.Textarea,   rows="2"),
        }


class SalesInvoiceForm(forms.ModelForm):
    class Meta:
        model  = SalesInvoice
        fields = [
            "date", "client_name","client_phone",
            "description","gross_amount","amount_paid","payment_status",
            "etims_registered","etims_cu_invoice_no","notes",
        ]
        widgets = {
            "date":                _w(forms.DateInput,   type="date"),
            # Made read-only with a clear descriptive placeholder and styled to indicate it's locked
            "invoice_number":      _w(forms.TextInput,   placeholder="[ Auto-Generated on Save ]", readonly="readonly", css_class="bg-stone-50 cursor-not-allowed"),
            "client_name":         _w(forms.TextInput,   placeholder="Client full name"),
            "client_phone":        _w(forms.TextInput,   placeholder="+254 7XX XXX XXX"),
            "description":         _w(forms.Textarea,    rows="2", placeholder="Goods / services sold"),
            "gross_amount":        _w(forms.NumberInput, step="0.01", min="0"),
            "amount_paid":         _w(forms.NumberInput, step="0.01", min="0"),
            "payment_status":      _w(forms.Select),
            "etims_registered":    forms.CheckboxInput(attrs={"class": "h-4 w-4 accent-amber-500"}),
            "etims_cu_invoice_no": _w(forms.TextInput,   placeholder="eTIMS CU number"),
            "notes":               _w(forms.Textarea,    rows="2"),
        }


class DrawingsForm(forms.ModelForm):
    class Meta:
        model  = DrawingsLog
        fields = ["month","year","amount","notes"]
        widgets = {
            "month":  _w(forms.NumberInput, min="1", max="12"),
            "year":   _w(forms.NumberInput, min="2020"),
            "amount": _w(forms.NumberInput, step="0.01", min="0"),
            "notes":  _w(forms.Textarea, rows="2"),
        }


class PeriodSelectForm(forms.Form):
    """Month/year picker for the dashboard."""
    MONTH_CHOICES = [(i, __import__("calendar").month_name[i]) for i in range(1, 13)]
    YEAR_CHOICES  = [(y, y) for y in range(2024, 2031)]

    month = forms.ChoiceField(choices=MONTH_CHOICES, widget=forms.Select(attrs={"class": _cls}))
    year  = forms.ChoiceField(choices=YEAR_CHOICES,  widget=forms.Select(attrs={"class": _cls}))
    nssf  = forms.DecimalField(
        required=False, initial=0, min_value=0,
        label="NSSF voluntary contribution (KES)",
        widget=forms.NumberInput(attrs={"class": _cls, "step": "0.01", "placeholder": "0"}),
    )
    use_drawings = forms.BooleanField(
        required=False, initial=False,
        label="Use drawings log for AHL base (instead of net profit)",
        widget=forms.CheckboxInput(attrs={"class": "h-4 w-4 accent-amber-500"}),
    )
