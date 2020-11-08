import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.decorators.http import require_POST

from SalsaVerde.common.views import display_dt
from SalsaVerde.company.models import Company

session = requests.Session()
logger = logging.getLogger('salsa.shopify')


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


@require_POST
def callback(request: WSGIRequest):
    from SalsaVerde.orders.shopify import process_shopify_event

    company = Company.objects.filter(
        shopify_domain=request.headers.get('X-Shopify-Shop-Domain'), shopify_domain__isnull=False
    ).first()
    if company and (key := company.shopify_webhook_key):
        data = request.POST
        sig = hmac.new(key.encode(), json.dumps(data).encode(), hashlib.sha256).digest()
        if not secrets.compare_digest(sig, request.headers.get('X-Shopify-Hmac-Sha256', '')):
            raise PermissionDenied('Invalid signature')
        topic = request.headers.get('X-Shopify-Topic', 'No/Topic')
        msg, status = process_shopify_event(topic, data, company=company)
        logger.info('Shopify event status %s:%s', status, msg)
    else:
        status = 299
        msg = 'Company with key does not exist'
    return HttpResponse(msg, status=status)
