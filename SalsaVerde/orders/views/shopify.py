import logging
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils.timezone import now
from django.views.generic import TemplateView
from operator import itemgetter
from urllib.parse import urlencode

from SalsaVerde.orders.models import Order
from SalsaVerde.stock.views.base_views import DisplayHelpers, display_dt

session = requests.Session()
logger = logging.getLogger('salsa-verde.orders')


def shopify_request(url, method='GET', data=None):
    logger.info(f'Making request to Shopify {url}')
    url = f'{settings.SHOPIFY_BASE_URL}/{url}'
    data = data or {}
    if method == 'GET':
        r = session.request(method, url, auth=(settings.SHOPIFY_API_KEY, settings.SHOPIFY_PASSWORD))
    else:
        r = session.request(method, url, auth=(settings.SHOPIFY_API_KEY, settings.SHOPIFY_PASSWORD), json=data)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        logger.warning('Request to Shopify failed: %r', r.content.decode())
        return False, r.content.decode()
    return True, r.json()


def get_shopify_order(id):
    items = ','.join(
        [
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
        ]
    )
    return shopify_request(f'orders/{id}.json?fields={items}')


class ShopifyHelperMixin:
    def get_shopify_url(self, order):
        return f"{self.request.user.company.website}/admin/orders/{order['id']}"

    def dt_format(self, v):
        return display_dt(datetime.strptime(v[:], '%Y-%m-%dT%H:%M:%S%z'))


class ShopifyOrdersView(ShopifyHelperMixin, DisplayHelpers, TemplateView):
    template_name = 'order_list.jinja'
    title = 'Shopify Orders'

    def get_orders(self):
        fields = 'name,created_at,billing_address,shipping_address,total_price,fulfillment_status,id'
        args = {
            'created_at_min': now().date() - relativedelta(weeks=1),
            'limit': 250,
            'status': 'any',
            'fields': fields,
        }
        _, data = shopify_request('orders.json?' + urlencode(args))
        order_lu = {o.shopify_id: o for o in Order.objects.request_qs(self.request)}
        for order in data['orders']:
            if sv_order := order_lu.get(str(order['id'])):
                order.update(**sv_order.order_info)
        yield from sorted(data['orders'], key=itemgetter('created_at'), reverse=True)

    def get_location(self, order):
        shipping_address = order['shipping_address']
        return f"{shipping_address['city']}, {shipping_address['country_code']}"

    def created_at(self, dt):
        return datetime.fromisoformat(dt).strftime(settings.DATE_FORMAT)


shopify_orders = ShopifyOrdersView.as_view()


def shopify_fulfill_order(order: Order):
    # Location is hard coded here as it doesn't change
    assert order.shopify_id
    data = {
        'fulfillment': {
            'location_id': 5032451,
            'tracking_number': order.shipping_id,
            'tracking_urls': order.tracking_url,
            'notify_customer': True,
        }
    }
    return shopify_request(f'orders/{order.shopify_id}/fulfillments.json', method='POST', data=data)
