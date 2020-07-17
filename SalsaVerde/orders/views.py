import logging
from datetime import datetime
from operator import itemgetter
from urllib.parse import urlencode

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import TemplateView

from SalsaVerde.main.views.base_views import DisplayHelpers, SVFormView
from SalsaVerde.orders.forms import ExpressFreightLabelForm, DUBLIN_COUNTIES, IE_COUNTIES, NI_COUNTIES

session = requests.Session()
logger = logging.getLogger('SV.request')


def shopify_request(url):
    logger.info(f'Making request to Shopify {url}')
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
    r = session.get(f'{settings.EF_URL}/Token/GetNewToken?{urlencode(auth_data)}')
    r.raise_for_status()
    token = r.json()['bearerToken']
    cache.set('ef_auth_token', token, 86400)
    return token


def expressfreight_request(url, data=None, method='GET'):
    logger.info(f'Making request to ExpressFreight {url}')
    if not (token := cache.get('ef_auth_token')):
        token = get_ef_auth_token()
    if method == 'POST':
        r = session.post(url=f'{settings.EF_URL}/{url}', headers={'Authorization': f'Bearer {token}'}, json=data)
    else:
        r = session.get(url=f'{settings.EF_URL}/{url}', headers={'Authorization': f'Bearer {token}'})
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


class ExpressFreightLabelCreate(SVFormView, TemplateView):
    template_name = 'ef_order_form.jinja'
    form_class = ExpressFreightLabelForm
    title = 'Create shipping order'

    def get(self, request, *args, **kwargs):
        self.order_data = shopify_request(f'orders/{self.order_id}.json')
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.order_id = kwargs['order_id']
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            dublin_counties=dict(DUBLIN_COUNTIES),
            ie_counties=dict(IE_COUNTIES),
            ni_counties=dict(NI_COUNTIES),
        )
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order_id'] = self.order_id
        if not self.request.POST:
            kwargs.update(shopify_data=self.order_data['order'])
        return kwargs

    def form_valid(self, form):
        data = form.ef_form_data()
        debug(data)
        r_data = expressfreight_request('Consignment/CreateConsignment', data=data, method='POST')
        debug(r_data)
        messages.success(self.request, 'Order created')
        return redirect(reverse('shopify-orders'))


ef_label_create = ExpressFreightLabelCreate.as_view()
