from django import forms
from .models import PartnerApplication, DesignSubmission

KENYA_COUNTIES = [
    ("", "— Select County —"),
    ("Nairobi", "Nairobi"), ("Mombasa", "Mombasa"), ("Kisumu", "Kisumu"),
    ("Nakuru", "Nakuru"), ("Eldoret / Uasin Gishu", "Eldoret / Uasin Gishu"),
    ("Kiambu", "Kiambu"), ("Machakos", "Machakos"), ("Kajiado", "Kajiado"),
    ("Muranga", "Muranga"), ("Nyeri", "Nyeri"), ("Meru", "Meru"),
    ("Kisii", "Kisii"), ("Migori", "Migori"), ("Kakamega", "Kakamega"),
    ("Kilifi", "Kilifi"), ("Kwale", "Kwale"), ("Taita Taveta", "Taita Taveta"),
    ("Embu", "Embu"), ("Garissa", "Garissa"), ("Other", "Other"),
]


class PartnerApplicationForm(forms.ModelForm):
    county = forms.ChoiceField(choices=KENYA_COUNTIES)

    class Meta:
        model  = PartnerApplication
        fields = [
            "full_name", "business_name", "business_type",
            "email", "mobile", "whatsapp",
            "county", "town", "address_details",
            "approximate_clients", "message",
        ]
        widgets = {
            "full_name":           forms.TextInput(attrs={"placeholder": "Jane Mwangi"}),
            "business_name":       forms.TextInput(attrs={"placeholder": "Mwangi Interiors Ltd"}),
            "email":               forms.EmailInput(attrs={"placeholder": "jane@example.com"}),
            "mobile":              forms.TextInput(attrs={"placeholder": "+254 7XX XXX XXX"}),
            "whatsapp":            forms.TextInput(attrs={"placeholder": "+254 7XX XXX XXX (if different)"}),
            "town":                forms.TextInput(attrs={"placeholder": "Karen, Westlands, Kiambu…"}),
            "address_details":     forms.Textarea(attrs={"rows": 2, "placeholder": "Building name, road or landmarks"}),
            "approximate_clients": forms.TextInput(attrs={"placeholder": "e.g. 5–10 per month"}),
            "message":             forms.Textarea(attrs={"rows": 3, "placeholder": "Tell us about your typical projects and clientele…"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " partner-input").strip()


class DesignSubmissionForm(forms.ModelForm):
    class Meta:
        model  = DesignSubmission
        fields = [
            "project_title", "project_type",
            "description", "site_location",
            "expected_start_date", "expected_completion_date",
            "priority", "budget_range",
            "design_file_1", "design_file_2", "design_file_3",
        ]
        widgets = {
            "project_title":            forms.TextInput(attrs={"placeholder": "e.g. Karen Villa Master Bedroom"}),
            "description":              forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the scope of work, materials preferred, finishes…"}),
            "site_location":            forms.TextInput(attrs={"placeholder": "e.g. Karen, Nairobi"}),
            "expected_start_date":      forms.DateInput(attrs={"type": "date"}),
            "expected_completion_date": forms.DateInput(attrs={"type": "date"}),
            "budget_range":             forms.TextInput(attrs={"placeholder": "e.g. 150,000 – 300,000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " partner-input").strip()

    def clean(self):
        cleaned = super().clean()
        start  = cleaned.get("expected_start_date")
        finish = cleaned.get("expected_completion_date")
        if start and finish and finish <= start:
            raise forms.ValidationError("Completion date must be after the start date.")
        return cleaned
