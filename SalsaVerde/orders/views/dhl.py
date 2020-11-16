import base64
import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile

from SalsaVerde.company.models import Company
from SalsaVerde.orders.forms.dhl import DHLLabelForm
from SalsaVerde.orders.views.common import CreateOrderView, CreateShipmentError
from SalsaVerde.stock.models import Document

session = requests.Session()
logger = logging.getLogger('salsa.orders')


def dhl_request(url, company: Company, data=None, method='GET'):
    if not company.dhl_api_key:
        return False, {'error': 'No API key added'}
    logger.info(f'Making request to DHL {url}')
    url = f'{settings.DHL_BASE_URL}/{url}'
    data = data or {}
    if method == 'GET':
        r = session.request(method, url, auth=(company.dhl_api_key, company.dhl_password))
    else:
        r = session.request(method, url, auth=(company.dhl_api_key, company.dhl_password), json=data)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        logger.warning('Request to DHL failed: status=%d response=%r', r.status_code, r.content.decode())
        return False, r.content.decode()
    return True, r.json()


def remove_null_vals(data):
    new_data = {}

    def _remove_null(_data):
        for k, v in _data.items():
            if isinstance(v, dict):
                new_data[k] = remove_null_vals(v)
            elif isinstance(v, list):
                new_data[k] = [remove_null_vals(_v) for _v in v]
            elif v not in {None, ''}:
                new_data[k] = v

    _remove_null(data)
    return new_data


class DHLCreateOrder(CreateOrderView):
    template_name = 'dhl_order_form.jinja'
    form_class = DHLLabelForm

    def create_shipment(self, form, package_form):
        cd = form.cleaned_data
        company = self.request.user.company
        contact = company.get_main_contact()
        data = {
            'plannedShippingDateAndTime': cd['dispatch_date'].strftime(
                '%Y-%m-%dT%H:%M:%S GMT+01:00'  # This is idiotic. We HAVE to use GMT.
            ),
            'pickup': {'isRequested': False},
            'productCode': cd['service_code'],
            'accounts': [{'number': company.dhl_account_code, 'typeCode': 'shipper'}],
            'customerDetails': {
                'shipperDetails': {
                    'postalAddress': {
                        'cityName': company.town,
                        'countryCode': company.country.iso_2,
                        'postalCode': company.postcode,
                        'addressLine1': company.street,
                    },
                    'contactInformation': {
                        'phone': company.phone,
                        'companyName': company.name,
                        'fullName': contact.get_full_name(),
                        'email': contact.email,
                    },
                },
                'receiverDetails': {
                    'postalAddress': {
                        'cityName': cd['town'],
                        'countryCode': cd['country'].iso_2,
                        'postalCode': cd['postcode'],
                        'addressLine1': cd['first_line'],
                        'addressLine2': cd['second_line'],
                        'addressLine3': cd['county'],
                    },
                    'contactInformation': {'phone': cd['phone'], 'companyName': cd['name'], 'fullName': cd['name']},
                },
            },
            'content': {
                'unitOfMeasurement': 'metric',
                'isCustomsDeclarable': False,
                'incoterm': 'DAP',
                'description': f'Order from {company.name}',
                'packages': [
                    {
                        'customerReferences': [
                            {'value': cd.get('shopify_id', f'Order from {company.name}'), 'typeCode': 'CU'}
                        ],
                        'weight': float(package['weight']),
                        'description': package['description'],
                        'dimensions': {
                            'length': float(package['length']),
                            'width': float(package['width']),
                            'height': float(package['height']),
                        },
                    }
                    for package in package_form.cleaned_data
                ],
            },
        }
        success, dhl_data = dhl_request(
            'shipments', self.request.user.company, data=remove_null_vals(data), method='POST'
        )
        if success:
            messages.success(self.request, 'Order created')
        else:
            messages.error(self.request, 'Error creating shipment: %r' % dhl_data)
            raise CreateShipmentError
        labels = dhl_data['documents']
        for label in labels:
            doc = Document(order=self.get_object(), author=self.request.user)
            doc.file.save('shipping_label.pdf', ContentFile(base64.b64decode(label['content'])), save=False)
            doc.save()


dhl_order_create = DHLCreateOrder.as_view()
