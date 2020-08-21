import base64
import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile

from SalsaVerde.orders.forms.dhl import DHLLabelForm
from SalsaVerde.orders.models import Order
from SalsaVerde.orders.views.common import CreateOrderView, CreateShipmentError
from SalsaVerde.stock.models import Document

session = requests.Session()
logger = logging.getLogger('salsa.orders')


def dhl_request(url, data=None, method='GET'):
    logger.info(f'Making request to DHL {url}')
    url = f'{settings.DHL_BASE_URL}/{url}'
    data = data or {}
    if method == 'GET':
        r = session.request(method, url, auth=(settings.DHL_API_KEY, settings.DHL_PASSWORD))
    else:
        r = session.request(method, url, auth=(settings.DHL_API_KEY, settings.DHL_PASSWORD), json=data)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        logger.warning('Request to DHL failed: %r', r.content.decode())
        return False, r.content.decode()
    return True, r.json()


class DHLCreateOrder(CreateOrderView):
    template_name = 'dhl_order_form.jinja'
    form_class = DHLLabelForm

    def create_shipment(self, form, package_form):
        cd = form.cleaned_data
        company = self.request.user.company
        contact = company.get_main_contact()
        data = {
            'plannedShippingDateAndTime': cd['dispatch_date'].isoformat(),
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

        success, dhl_data = dhl_request('shipments', data=data, method='POST')
        if success:
            messages.success(self.request, 'Order created')
        else:
            messages.error(self.request, 'Error creating shipment: %r' % dhl_data)
            raise CreateShipmentError
        labels = dhl_data['documents']
        order = Order.objects.create(
            shopify_id=self.shopify_order_id,
            shipping_id=dhl_data['shipmentTrackingNumber'],
            tracking_url=dhl_data['trackingUrl'],
            company=self.request.user.company,
        )
        for label in labels:
            doc = Document(order=order, author=self.request.user)
            doc.file.save('shipping_label.pdf', ContentFile(base64.b64decode(label['content'])), save=False)
            doc.save()
        return order


dhl_order_create = DHLCreateOrder.as_view()
