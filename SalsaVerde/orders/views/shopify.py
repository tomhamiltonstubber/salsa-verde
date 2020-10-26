import logging
from datetime import datetime
from urllib.parse import urlencode

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils.timezone import now
from django_rq import job

from SalsaVerde.common.views import display_dt
from SalsaVerde.orders.models import Order

session = requests.Session()
logger = logging.getLogger('salsa.orders')


def shopify_request(url, method='GET', data=None):
    logger.info(f'Making request to Shopify {url}')
    url = f'{settings.SHOPIFY_BASE_URL}/{url}'
    data = data or {}
    if method == 'GET':
        if data:
            url += f'?{urlencode(data)}'
        r = session.request(method, url, auth=(settings.SHOPIFY_API_KEY, settings.SHOPIFY_PASSWORD))
    else:
        r = session.request(method, url, auth=(settings.SHOPIFY_API_KEY, settings.SHOPIFY_PASSWORD), json=data)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        logger.warning('Request to Shopify failed: %r', r.content.decode())
        return False, r.content.decode()
    return True, r.json()


ORDER_FIELDS = [
    'name',
    'billing_address',
    'shipping_address',
    'id',
    'line_items',
    'quantity',
    'price',
    'total_line_items_price',
    'total_discounts',
    'total_price',
    'created_at',
    'fulfillment_status',
    'shipping_lines',
]


def get_shopify_order(id):
    return shopify_request(f"orders/{id}.json?fields={','.join(ORDER_FIELDS)}")


def get_shopify_orders(status: str):
    args = {
        'created_at_min': now().date() - relativedelta(weeks=1),
        'limit': 50,
        'status': 'any',
        'fields': ','.join(ORDER_FIELDS),
        'fulfillment_status': status,
    }
    return shopify_request('orders.json?', data=args)


class ShopifyHelperMixin:
    def get_shopify_url(self, order_id: str):
        return f"{self.request.user.company.website}/admin/orders/{order_id}"

    def dt_format(self, v):
        return display_dt(datetime.strptime(v, '%Y-%m-%dT%H:%M:%S%z'))


@job
def shopify_fulfill_order(order: Order):
    # Location is hard coded here as it doesn't change
    assert order.shopify_id
    data = {
        'fulfillment': {
            'location_id': 5032451,
            'tracking_number': order.shipping_id,
            'tracking_urls': [order.tracking_url],
            'notify_customer': True,
        }
    }
    success, content = shopify_request(f'orders/{order.shopify_id}/fulfillments.json', method='POST', data=data)
    if success:
        order.fulfilled = True
        order.save()
    else:
        logger.error('Error fulfilling Shopify order: %s', content)
