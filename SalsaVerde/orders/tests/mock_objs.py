import re

from requests.exceptions import HTTPError


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
                return {
                    'consignmentNumber': 'EF_123',
                    'trackingLink': 'https://foobar.com/EF_123',
                    'labels': ['https://foobar.com/EF_123_L1', 'https://foobar.com/EF_123_L2'],
                }

    return FakeExpressFreight


def fake_shopify(error=False):
    class MockShopify:
        def __init__(self, method, url, auth, json=None):
            self.url = url
            self.method = method
            self.orders = [
                {
                    'id': 123,
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

        def raise_for_status(self):
            if error:
                raise HTTPError('Bah humbug')

        def json(self):
            if re.match(r'.*orders/(\d+)\.json', self.url) and self.method == 'GET':
                return {'order': self.orders[0]}
            elif re.match(r'.*orders\.json', self.url) and self.method == 'GET':
                return {'orders': self.orders}

    return MockShopify
