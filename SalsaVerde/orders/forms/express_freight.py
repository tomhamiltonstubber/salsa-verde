import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now

from SalsaVerde.stock.forms.base_forms import SVForm

DUBLIN_COUNTIES = [(f'DUBLIN {i}', f'Dublin {i}') for i in range(1, 24)]
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
    region = forms.ChoiceField(choices=[('REST OF IRELAND', 'ROI'), ('NORTH IRELAND', 'NI'), ('DUBLIN', 'Dublin')])
    county = forms.ChoiceField(choices=sorted(DUBLIN_COUNTIES + IE_COUNTIES + NI_COUNTIES))
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
            if any('dublin' in c.lower() for c in {address['city'], address['province']} if c):
                self.fields['region'].initial = 'DUBLIN'
            elif address['zip'].lower().startswith('bt'):
                self.fields['region'].initial = 'NORTH IRELAND'
            self.fields['shopify_order'].initial = order_id
        # self.fields['dispatch_date'].widget.attrs = {'daysOfWeekDisabled': [0, 6], 'format': 'LT'}

    def clean_phone(self):
        if phone := self.cleaned_data.get('phone'):
            return re.sub('[^0-9]+', '', phone.replace('+', '00'))

    def clean(self):
        for field in ['first_line', 'second_line', 'town', 'postcode']:
            if v := self.cleaned_data.get(field):
                self.cleaned_data[field] = re.sub('[^A-Za-z0-9 ]+', '', v)
        return self.cleaned_data

    def clean_county(self):
        if self.cleaned_data.get('region', '') == 'DUBLIN' and not self.cleaned_data.get('county').startswith('DUBLIN'):
            raise ValidationError('If the customer is in Dublin, you have to choose a Dublin county.')
        return self.cleaned_data.get('county')

    def clean_dispatch_date(self):
        if dt := self.cleaned_data.get('dispatch_date'):
            return dt.date().strftime('%Y-%m-%d')
