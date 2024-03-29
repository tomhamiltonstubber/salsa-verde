import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from SalsaVerde.common.views import display_dt
from SalsaVerde.company.models import Company

session = requests.Session()
logger = logging.getLogger('salsa.shopify')


def shopify_request(url, method='GET', data=None, *, company: Company, retries=0):
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
    if not (str(r.status_code).startswith('2')) or 'errors' in r.content.decode():
        if retries == 5:
            logger.warning('Request to Shopify failed after 5 attempts: %r', r.content.decode())
            return False, r.content.decode()
        else:
            time.sleep(1)
            shopify_request(url, method='GET', data=None, company=company, retries=retries + 1)
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
        return f'{self.request.user.company.website}/admin/orders/{order_id}'

    def dt_format(self, v):
        if v:
            return display_dt(datetime.strptime(v, '%Y-%m-%dT%H:%M:%S%z'))


@require_POST
@csrf_exempt
def callback(request: WSGIRequest):
    from SalsaVerde.orders.shopify import process_shopify_event

    domain = request.headers.get('X-Shopify-Shop-Domain')
    company = Company.objects.filter(shopify_domain=domain, shopify_domain__isnull=False).first()
    if company and (key := company.shopify_webhook_key):
        data = json.loads(request.body.decode())
        sig = request.headers.get('X-Shopify-Hmac-Sha256', '')
        sig = sig.encode() if isinstance(sig, str) else sig
        m = hmac.new(key.encode(), request.body, hashlib.sha256).hexdigest()
        if not secrets.compare_digest(m.encode(), sig):
            logger.error('Invalid signature for data', extra={'shopify_data': data, 'received_sig': sig, 'sig': m})
            # raise PermissionDenied('Invalid signature')
        topic = request.headers.get('X-Shopify-Topic', 'No/Topic')
        try:
            msg, status = process_shopify_event(topic, data, company=company)
        except Exception as e:
            logger.error('Error processing data', exc_info=e, extra={'shopify_data': data})
            raise
    else:
        status = 299
        msg = f'Company with domain {domain} does not exist'
    logger.info('Shopify event status %s:%s', status, msg)
    return HttpResponse(msg, status=status)
