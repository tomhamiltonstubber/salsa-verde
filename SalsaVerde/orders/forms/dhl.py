from django import forms
from django.utils.timezone import now

from SalsaVerde.company.models import Country
from SalsaVerde.stock.forms.base_forms import SVForm

DHL_SERVICE_CODES = (
    ('N', 'Domestic Express'),
    ('1', 'Domestic Express 12:00'),
    ('I', 'Domestic Express 9:00'),
    ('U', 'Europe Express'),
    ('T', 'Europe Express 12:00'),
    ('K', 'Europe Express 9:00'),
    ('P', 'ROW Express'),
    ('Y', 'ROW Express 12:00'),
    ('E', 'ROW Express 9:00'),
)


class DHLLabelForm(SVForm):
    shopify_order = forms.CharField(widget=forms.HiddenInput, required=False)
    service_code = forms.ChoiceField(choices=DHL_SERVICE_CODES)
    name = forms.CharField()
    phone = forms.CharField()
    first_line = forms.CharField()
    second_line = forms.CharField(required=False)
    town = forms.CharField()
    postcode = forms.CharField()
    county = forms.CharField(required=False)
    country = forms.ModelChoiceField(Country.objects.all())
    dispatch_date = forms.DateTimeField(initial=now())

    def __init__(self, order_id=None, shopify_data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if shopify_data:
            address = shopify_data.get('shipping_address')
            self.fields['name'].initial = address['name']
            self.fields['first_line'].initial = address['address1']
            self.fields['second_line'].initial = address['address2']
            self.fields['town'].initial = address['city']
            self.fields['county'].initial = address['province']
            self.fields['postcode'].initial = address['zip']
            self.fields['phone'].initial = address['phone']
            self.fields['shopify_order'].initial = order_id
            self.fields['country'].initial = Country.objects.filter(iso_2=address['country_code']).first()
