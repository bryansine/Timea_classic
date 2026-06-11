from django import forms
import re

class GuestCheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone_number = forms.CharField(
        max_length=13,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0712345678'}),
        help_text="Enter M-Pesa number for payment prompt."
    )
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Delivery Details / Location'}))

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number').strip().replace(" ", "")
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+254'):
            phone = phone[1:]
            
        if not re.match(r'^254(7|1)\d{8}$', phone):
            raise forms.ValidationError("Please enter a valid M-Pesa phone number (e.g., 07XXXXXXXX).")
        return phone