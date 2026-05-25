from django import forms
from .models import Enquiry, BidderProfile


FIELD_CLASS = 'w-full px-4 py-3 rounded-lg bg-stone-800 border border-stone-600 text-white placeholder-stone-400 focus:outline-none focus:border-amber-500 transition'


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['name', 'phone', 'email', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': 'Your full name', 'class': FIELD_CLASS}),
            'phone':   forms.TextInput(attrs={'placeholder': '+254 7XX XXX XXX', 'class': FIELD_CLASS}),
            'email':   forms.EmailInput(attrs={'placeholder': 'your@email.com (optional)', 'class': FIELD_CLASS}),
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us what you need...', 'class': FIELD_CLASS + ' resize-none'}),
        }


class BidderProfileForm(forms.ModelForm):
    class Meta:
        model = BidderProfile
        fields = ['name', 'phone', 'email']
        widgets = {
            'name':  forms.TextInput(attrs={'placeholder': 'Your full name *', 'class': FIELD_CLASS}),
            'phone': forms.TextInput(attrs={'placeholder': '+254 7XX XXX XXX *', 'class': FIELD_CLASS}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email (optional)', 'class': FIELD_CLASS}),
        }


class BidForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter your bid amount (KSh)',
            'class': FIELD_CLASS,
            'step': '500',
            'min': '0',
        })
    )

    def __init__(self, *args, auction=None, **kwargs):
        super().__init__(*args, **kwargs)
        if auction:
            self.fields['amount'].min_value = float(auction.minimum_next_bid)
            self.fields['amount'].widget.attrs['min'] = float(auction.minimum_next_bid)
            self.fields['amount'].widget.attrs['placeholder'] = (
                f'Min bid: KSh {auction.minimum_next_bid:,.0f}'
            )
