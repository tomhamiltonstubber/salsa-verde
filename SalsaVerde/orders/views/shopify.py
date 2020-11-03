import hashlib
import hmac
import logging
import secrets
from datetime import datetime
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from requests import Request

from SalsaVerde.common.views import display_dt
from SalsaVerde.company.models import Company

session = requests.Session()
logger = logging.getLogger('salsa.orders')


def shopify_request(url, method='GET', data=None, *, company: Company):
    logger.info(f'Making request to Shopify {url}')
    url = f'{settings.SHOPIFY_BASE_URL}/{url}'
    data = data or {}
    if not (company.shopify_api_key and company.shopify_password):
        return False, 'No API key for company'
    else:
        auth = (company.shopify_api_key, company.shopify_password)
    if method == 'GET':
        if data:
            url += f'?{urlencode(data)}'
        r = session.request(method, url, auth=auth)
    else:
        r = session.request(method, url, auth=auth, json=data)
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
    'customer',
    'total_line_items_price',
    'total_discounts',
    'total_price',
    'created_at',
    'fulfillment_status',
    'shipping_lines',
]


def get_shopify_order(id, company: Company):
    return shopify_request(f"orders/{id}.json?fields={','.join(ORDER_FIELDS)}", company=company)


class ShopifyHelperMixin:
    def get_shopify_url(self, order_id: str):
        return f"{self.request.user.company.website}/admin/orders/{order_id}"

    def dt_format(self, v):
        return display_dt(datetime.strptime(v, '%Y-%m-%dT%H:%M:%S%z'))


def callback(request: Request):
    from SalsaVerde.orders.shopify import process_order_event

    if not settings.SHOPIFY_WEBHOOK_KEY:
        return HttpResponse('ok')

    sig = hmac.new(settings.SHOPIFY_WEBHOOK_KEY, request.data, hashlib.sha256).digest()
    if not secrets.compare_digest(sig, request.headers.get('X-Shopify-Hmac-Sha256')):
        raise PermissionDenied('Invalid signature')

    topic = request.headers.get('X-Shopify-Topic', '/')
    company = Company.objects.filter(shopify_domain=request.headers.get('X-Shopify-Shop-Domain')).first()
    if company:
        status, msg = process_order_event(topic, request.data, company=company)
    else:
        status = 221
        msg = 'Company does not exist'

    logger.info('Shopify event status %s:%s', status, msg)
    return HttpResponse(msg, status=status)
