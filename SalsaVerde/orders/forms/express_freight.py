import re

from django import forms
from django.utils.timezone import now

from SalsaVerde.stock.forms.base_forms import SVForm

NI_COUNTIES = [
    ('CO. ANTRIM', 'Antrim'),
    ('CO. ARMAGH', 'Armagh'),
    ('CO. DOWN', 'Down'),
    ('CO. FERMANAGH', 'Fermanagh'),
    ('CO. DERRY', 'Derry'),
    ('CO. TYRONE', 'Tyrone'),
]
IE_COUNTIES = [
    ('CO. CARLOW', 'Carlow'),
    ('CO. CAVAN', 'Cavan'),
    ('CO. CLARE', 'Clare'),
    ('CO. CORK', 'Cork'),
    ('CO. DONEGAL', 'Donegal'),
    ('CO. DUBLIN', 'Dublin'),
    ('CO. GALWAY', 'Galway'),
    ('CO. KERRY', 'Kerry'),
    ('CO. KILDARE', 'Kildare'),
    ('CO. KILKENNY', 'Kilkenny'),
    ('CO. LAOIS', 'Laois'),
    ('CO. LEITRIM', 'Leitrim'),
    ('CO. LIMERICK', 'Limerick'),
    ('CO. LONGFORD', 'Longford'),
    ('CO. LOUTH', 'Louth'),
    ('CO. MAYO', 'Mayo'),
    ('CO. MEATH', 'Meath'),
    ('CO. MONAGHAN', 'Monaghan'),
    ('CO. OFFALY', 'Offaly'),
    ('CO. ROSCOMMON', 'Roscommon'),
    ('CO. SLIGO', 'Sligo'),
    ('CO. TIPPERARY', 'Tipperary'),
    ('CO. WATERFORD', 'Waterford'),
    ('CO. WESTMEATH', 'Westmeath'),
    ('CO. WEXFORD', 'Wexford'),
    ('CO. WICKLOW', 'Wicklow'),
]


class ExpressFreightLabelForm(SVForm):
    shopify_order = forms.CharField(widget=forms.HiddenInput, required=False)
    name = forms.CharField()
    first_line = forms.CharField()
    second_line = forms.CharField(required=False)
    town = forms.CharField(help_text='Note that anything other than letters will be removed from this.')
    region = forms.ChoiceField(choices=[('REST OF IRELAND', 'ROI'), ('NORTH IRELAND', 'NI')])
    county = forms.ChoiceField(choices=[(None, '---------')] + IE_COUNTIES + NI_COUNTIES)
    postcode = forms.CharField(required=False)
    phone = forms.CharField()
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

    def clean_phone(self):
        if phone := self.cleaned_data.get('phone'):
            return re.sub('[^0-9]+', '', phone.replace('+', '00'))

    def clean(self):
        for field in ['first_line', 'second_line', 'town', 'postcode']:
            if v := self.cleaned_data.get(field):
                self.cleaned_data[field] = re.sub('[^A-Za-z0-9 ]+', '', v)
        return self.cleaned_data

    def clean_dispatch_date(self):
        if dt := self.cleaned_data.get('dispatch_date'):
            return dt.date().strftime('%Y-%m-%d')
