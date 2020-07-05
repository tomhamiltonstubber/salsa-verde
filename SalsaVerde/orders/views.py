from datetime import datetime
from operator import itemgetter
from urllib.parse import urlencode

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now
from django.views.generic import TemplateView

from SalsaVerde.main.views.base_views import DisplayHelpers

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


def expressfreight_request(url):
    if not (token := cache.get('ef_auth_token')):
        token = get_ef_auth_token()
    r = session.get(f'{settings.EF_URL}/{url}', headers={'Authorization': f'Bearer {token}'})
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


class ExpressFreightLabelCreator(DisplayHelpers, TemplateView):
    pass
