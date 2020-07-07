from datetime import datetime
from operator import itemgetter
from urllib.parse import urlencode

import requests
from dateutil.relativedelta import relativedelta
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.timezone import now
from django.views.generic import TemplateView

from SalsaVerde.main.views.base_views import DisplayHelpers, SVFormView

session = requests.Session()


def shopify_request(url):
    r = session.get(f'{settings.SHOPIFY_BASE_URL}/{url}', auth=(settings.SHOPIFY_API_KEY, settings.SHOPIFY_PASSWORD))
    r.raise_for_status()
    return r.json()


def get_ef_auth_token():
    auth_data = {
        'ClientID': settings.EF_CLIENT_ID,
        'ClientSecret': settings.EF_CLIENT_SECRET,
        'username': settings.EF_USERNAME,
        'password': settings.EF_PASSWORD,
    }
    data = expressfreight_request(f'/Token/GetNewToken?{urlencode(auth_data)}')
    token = data['bearerToken']
    cache.set('ef_auth_token', token, 86400)
    return token


def expressfreight_request(url, data, method='GET'):
    if not (token := cache.get('ef_auth_token')):
        token = get_ef_auth_token()
    if method == 'POST':
        r = session.post(url=f'{settings.EF_URL}/{url}', headers={'Authorization': f'Bearer {token}'}, json=data)
    else:
        r = session.get(url=f'{settings.EF_URL}/{url}', headers={'Authorization': f'Bearer {token}'})
    debug(r.content.decode())
    r.raise_for_status()
    return r.json()


class ShopifyOrdersView(DisplayHelpers, TemplateView):
    template_name = 'order_list.jinja'
    title = 'Shopify Orders'

    def get_orders(self):
        data = shopify_request('orders.json?' + urlencode(
            {'created_at_min': now() - relativedelta(months=1), 'limit': 250}
        ))
        yield from sorted(data['orders'], key=itemgetter('created_at'), reverse=True)

    def get_location(self, order):
        shipping_address = order['shipping_address']
        return f"{shipping_address['city']}, {shipping_address['country_code']}"

    def created_at(self, dt):
        return datetime.fromisoformat(dt).strftime('%d-%m-%y')


shopify_orders = ShopifyOrdersView.as_view()


class ExpressFreightLabelForm(forms.Form):
    shopify_order = forms.CharField(label='Shopify Order ID', disabled=True)
    name = forms.CharField()
    first_line = forms.CharField()
    second_line = forms.CharField()
    town = forms.CharField()
    county = forms.CharField()
    postcode = forms.CharField()
    country = forms.ChoiceField(choices=[('NORTH IRELAND', 'NI'), ('REST OF IRELAND', 'ROI')])
    phone = forms.CharField()
    item_type = forms.ChoiceField(choices=[('carton', 'Carton'), ('pallet', 'Pallet')])
    item_count = forms.IntegerField()
    despatch_date = forms.DateField()

    def __init__(self, shopify_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        address = shopify_data['shipping_address']
        self.fields['name'].initial = address['first_name'] + address['last_name']
        self.fields['first_line'].initial = address['address1']
        self.fields['second_line'].initial = address['address2']
        self.fields['town'].initial = address['city']
        self.fields['county'].initial = address['province']
        self.fields['postcode'].initial = address['zip']
        self.fields['phone'].initial = address['phone']
        self.fields['despatch_date'].widget.attrs = {'daysOfWeekDisabled': [0, 6], 'format': 'LT'}


class ExpressFreightLabelCreate(SVFormView, TemplateView):
    template_name = 'ef-label-create.jinja'
    form_class = ExpressFreightLabelForm

    def get(self, request, *args, **kwargs):
        self.order_data = shopify_request(f"orders/{kwargs['order_id']}.json")
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(shopify_order=self.order_data)
        return kwargs

    def form_valid(self, form):
        cd = form.cleaned_data
        data = {
            'consigneeName': cd['name'],
            'consigneeStreet': cd['first_line'],
            'consigneeStreet2': cd['second_line'],
            'consigneeCity': cd['town'],
            'consigneeCounty': cd['province'],
            'consigneePostcode': cd['postcode'],
            'contactName': cd['name'],
            'contactNo': cd['phone'],
            'orderReference': self.order_data['id'],
            'serviceType': 'STANDARD',
            'consigneeRegion': cd['country'],
            'items': [
                {
                    'itemType': cd['item_type'],
                    'itemWeight': 0,
                    'itemHeight': 0,
                    'itemWidth': 0,
                    'itemLength': 0,
                    'dangerousGoods': False,
                } for _ in cd['item_count']
            ]
        }
        data = expressfreight_request('api/Consignment/CreateConsignment', data=data, method='POST')
        debug(data)
        return redirect('/')


ef_label_create = ExpressFreightLabelCreate.as_view()
