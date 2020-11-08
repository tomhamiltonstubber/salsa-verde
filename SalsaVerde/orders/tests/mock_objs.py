import base64
import re
from pathlib import Path

from requests.exceptions import HTTPError

THIS_DIR = Path(__file__).parent.resolve()


def fake_dhl(error=False):
    class FakeDHL:
        def __init__(self, method, url, json=None, headers=None, **kwargs):
            self.url = url
            self.method = method
            self.headers = headers

        def raise_for_status(self):
            if error:
                raise HTTPError('Bah humbug')

        def json(self):
            if re.match(r'.*shipments', self.url) and self.method == 'POST':
                with open(THIS_DIR / 'testing.pdf', 'rb') as f:
                    content = f.read()
                content = base64.b64encode(content).decode()
                return {
                    'shipmentTrackingNumber': 'DHL_123',
                    'trackingUrl': 'https://foobar.com/DHL_123',
                    'documents': [{'name': 'Foobar', 'content': content}, {'name': 'Barfoo', 'content': content}],
                }

    return FakeDHL


def fake_ef(error=False):
    class FakeExpressFreight:
        def __init__(self, method, url, json=None, headers=None, **kwargs):
            self.url = url
            self.method = method
            self.headers = headers

        def raise_for_status(self):
            if error:
                raise HTTPError('Bah humbug')

        def json(self):
            if re.match(r'.*GetNewToken', self.url) and self.method == 'GET':
                return {'bearerToken': 'AuthToken'}
            elif re.match(r'.*Consignment/CreateConsignment', self.url) and self.method == 'POST':
                with open(THIS_DIR / 'testing.pdf', 'rb') as f:
                    content = f.read()
                content = base64.b64encode(content).decode()
                return {
                    'consignmentNumber': 'EF_123',
                    'trackingLink': 'https://foobar.com/EF_123',
                    'labels': [content, content],
                }

    return FakeExpressFreight


def fake_shopify(error=False):
    class MockShopify:
        orders = [
            {
                'id': '123',
                'name': '#123',
                'created_at': '2020-08-19T08:47:12+01:00',
                'total_price': '40.50',
                'total_discounts': '4.50',
                'total_line_items_price': '45.00',
                'fulfillment_status': None,
                'line_items': [
                    {'quantity': 5, 'name': 'Bramley apple infused Balsamic Vinegar - 250ml', 'price': '9.00'},
                ],
                'shipping_address': {
                    'address1': '123 Fake st',
                    'phone': '07714 123456',
                    'city': 'Belfast',
                    'zip': 'BT72 2LL',
                    'province': None,
                    'country': 'United Kingdom',
                    'address2': '',
                    'name': 'Brain Johnston',
                    'country_code': 'GB',
                },
                'customer': {
                    'email': 'brain_johnston@fakemail.com',
                    'last_name': 'Johnston',
                    'first_name': 'Brain',
                },
                'billing_address': {
                    'address1': '123 Fake st',
                    'phone': '07714 123456',
                    'city': 'Belfast',
                    'zip': 'BT72 2LL',
                    'province': None,
                    'country': 'United Kingdom',
                    'address2': '',
                    'name': 'Brain Johnston',
                    'country_code': 'GB',
                },
            },
            {
                'id': '456',
                'created_at': '2020-08-19T08:47:12+01:00',
                'total_price': '40.50',
                'total_discounts': '4.50',
                'total_line_items_price': '45.00',
                'fulfillment_status': 'fulfilled',
                'name': '#456',
                'line_items': [
                    {'quantity': 5, 'name': 'Bramley apple infused Balsamic Vinegar - 250ml', 'price': '9.00'},
                ],
                'customer': {
                    'last_name': 'Jones',
                    'first_name': 'Tom',
                },
                'shipping_address': {
                    'address1': '123 Fake st',
                    'phone': '07714 123456',
                    'city': 'Belfast',
                    'zip': 'BT72 2LL',
                    'province': None,
                    'country': 'United Kingdom',
                    'address2': '',
                    'name': 'Brain Fulfilled',
                    'country_code': 'GB',
                },
                'billing_address': {
                    'address1': '123 Fake st',
                    'phone': '07714 123456',
                    'city': 'Belfast',
                    'zip': 'BT72 2LL',
                    'province': None,
                    'country': 'United Kingdom',
                    'address2': '',
                    'name': 'Brain Johnston',
                    'country_code': 'GB',
                },
            },
        ]

        def __init__(self, method, url, auth, json=None):
            self.url = url
            self.method = method

        def raise_for_status(self):
            if error:
                raise HTTPError('Bah humbug')

        def json(self):
            if re.match(r'.*orders/\d+\.json', self.url) and self.method == 'GET':
                order_id = re.search(r'orders/(\d+)\.json', self.url).group(1)
                return {'order': next(o for o in self.orders if o['id'] == order_id)}
            elif re.match(r'.*orders\.json', self.url) and self.method == 'GET':
                if 'shipped' in self.url:
                    return {'orders': [o for o in self.orders if o['fulfillment_status'] == 'fulfilled']}
                else:
                    return {'orders': [o for o in self.orders if not o['fulfillment_status']]}

    return MockShopify
