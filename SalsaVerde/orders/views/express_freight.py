import base64
import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.files.base import ContentFile

from SalsaVerde.company.models import Company
from SalsaVerde.orders.forms.express_freight import IE_COUNTIES, NI_COUNTIES, ExpressFreightLabelForm
from SalsaVerde.orders.views.common import CreateOrderView, CreateShipmentError
from SalsaVerde.stock.models import Document

session = requests.Session()
logger = logging.getLogger('salsa.orders')


def get_ef_auth_token(company: Company):
    if not company.ef_client_id:
        return False, {'error': 'No API key added'}
    auth_data = {
        'ClientID': company.ef_client_id,
        'ClientSecret': company.ef_client_secret,
        'username': company.ef_username,
        'password': company.ef_password,
    }
    r = session.get(f'{settings.EF_URL}/Token/GetNewToken?{urlencode(auth_data)}')
    r.raise_for_status()
    token = r.json()['bearerToken']
    cache.set('ef_auth_token', token, 3600)
    return token


def expressfreight_request(url, company: Company, data=None, method='GET'):
    logger.info(f'Making request to ExpressFreight {url}')
    if not (token := cache.get('ef_auth_token')):
        token = get_ef_auth_token(company)
    if method == 'POST':
        r = session.request(
            method, url=f'{settings.EF_URL}/{url}', headers={'Authorization': f'Bearer {token}'}, json=data
        )
    else:
        r = session.request(method, url=f'{settings.EF_URL}/{url}', headers={'Authorization': f'Bearer {token}'})
    try:
        r.raise_for_status()
    except requests.HTTPError:
        logger.error('Request to EF failed: %r', r.content.decode(), extra=data or {})
        return False, r.content.decode()
    return True, r.json()


class ExpressFreightCreateOrder(CreateOrderView):
    template_name = 'ef_order_form.jinja'
    form_class = ExpressFreightLabelForm

    def create_shipment(self, form, package_form):
        cd = form.cleaned_data
        data = {
            'consigneeName': cd['name'],
            'ConsigneeNumber': '',
            'ConsigneeTownland': '',
            'SpecialInstructions': '',
            'consigneeStreet': cd['first_line'],
            'consigneeStreet2': cd['second_line'] or '',
            'consigneeCity': cd['town'] or '',
            'consigneeCounty': cd['county'],
            'consigneePostcode': cd['postcode'] or '',
            'contactName': cd['name'],
            'contactNo': cd['phone'],
            'orderReference': cd['shopify_order'],
            'serviceType': 'STANDARD',
            'consigneeRegion': cd['region'],
            'dispatchDate': cd['dispatch_date'],
            'labelsLink': False,
            'items': [
                {
                    'itemType': 'CARTON',
                    'itemWeight': float(package['weight']),
                    'itemHeight': float(package['height']),
                    'itemWidth': float(package['width']),
                    'itemLength': float(package['length']),
                    'dangerousGoods': False,
                    'limitedQuantities': False,
                }
                for package in package_form.cleaned_data
            ],
        }

        success, ef_data = expressfreight_request(
            'Consignment/CreateConsignment', self.request.user.company, data=data, method='POST'
        )
        if success:
            messages.success(self.request, 'Order created')
        else:
            messages.error(self.request, 'Error creating shipment: %r' % ef_data)
            raise CreateShipmentError
        for label in ef_data['labels']:
            doc = Document(order=self.get_object(), author=self.request.user)
            doc.file.save('shipping_label.pdf', ContentFile(base64.b64decode(label)), save=False)
            doc.save()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            ie_counties={None: '-------', **dict(IE_COUNTIES)}, ni_counties={None: '------', **dict(NI_COUNTIES)}
        )
        return ctx


ef_order_create = ExpressFreightCreateOrder.as_view()
