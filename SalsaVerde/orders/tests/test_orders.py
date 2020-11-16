from datetime import datetime
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from SalsaVerde.company.models import User
from SalsaVerde.orders.factories.orders import OrderFactory
from SalsaVerde.orders.models import Order
from SalsaVerde.orders.tests.mock_objs import fake_dhl, fake_ef, fake_shopify
from SalsaVerde.stock.factories.company import CompanyFactory
from SalsaVerde.stock.factories.product import ProductFactory
from SalsaVerde.stock.factories.users import UserFactory
from SalsaVerde.stock.models import Document
from SalsaVerde.stock.tests.test_common import AuthenticatedClient, empty_formset


class DHLOrderTestCase(TestCase):
    def setUp(self):
        self.company = CompanyFactory(
            shopify_domain='https://company.shopify.com',
            shopify_webhook_key='foo',
            shopify_api_key='bar',
            shopify_password='pass',
            dhl_api_key='foo',
            dhl_password='bar',
            dhl_account_code='123abc',
        )
        self.client = AuthenticatedClient(company=self.company)
        self.orders_url = reverse('orders-list')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    @mock.patch('SalsaVerde.orders.views.dhl.session.request')
    def test_dhl_form_submit(self, mock_dhl, mock_shopify):
        shopify = fake_shopify()
        mock_shopify.side_effect = shopify
        mock_dhl.side_effect = fake_dhl()
        order = OrderFactory(company=self.company, shopify_id='123', extra_data=shopify.orders[0])
        r = self.client.get(reverse('fulfill-order-dhl', args=[order.pk]))
        self.assertContains(r, 'Brain Johnston')
        u = User.objects.get()
        u.town = 'Here'
        u.phone = '897987'
        u.email = 't@a.com'
        u.save()
        form_data = {
            'name': 'Brain Johnston',
            'first_line': '123 Fake Street.',
            'town': 'Bel fast',
            'county': 'Down',
            'phone': '+123789',
            'shopify_order': '123',
            'country': self.company.country.id,
            'service_code': 'N',
            'postcode': '12345',
            'dispatch_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'form-0-height': 5,
            'form-0-weight': 6,
            'form-0-length': 7,
            'form-0-width': 10,
            **empty_formset('form'),
        }
        r = self.client.post(reverse('fulfill-order-dhl', args=[order.pk]), follow=True, data=form_data)
        self.assertRedirects(r, self.orders_url)
        self.assertContains(r, 'Order created')
        order = Order.objects.get()
        assert order.shopify_id == '123'
        assert order.shipping_id == 'DHL_123'
        assert order.tracking_url == 'https://foobar.com/DHL_123'
        assert order.labels.count() == 2
        assert order.company == self.company
        call_args = mock_dhl.mock_calls[0][2]
        assert call_args == {
            'auth': (
                'demo-key',
                'demo-secret',
            ),
            'json': {
                'plannedShippingDateAndTime': '2018-02-02T00:00:00+00:00',
                'pickup': {'isRequested': False},
                'productCode': 'N',
                'accounts': [{'number': '123abc', 'typeCode': 'shipper'}],
                'customerDetails': {
                    'shipperDetails': {
                        'postalAddress': {
                            'cityName': 'Portafake',
                            'countryCode': 'GB',
                            'postalCode': '123abc',
                            'addressLine1': '123 Fake Street',
                        },
                        'contactInformation': {
                            'phone': '998877',
                            'companyName': 'company 0',
                            'fullName': 'Tom Owner',
                            'email': 't@a.com',
                        },
                    },
                    'receiverDetails': {
                        'postalAddress': {
                            'cityName': 'Bel fast',
                            'countryCode': 'GB',
                            'postalCode': '12345',
                            'addressLine1': '123 Fake Street.',
                            'addressLine2': '',
                            'addressLine3': 'Down',
                        },
                        'contactInformation': {
                            'phone': '+123789',
                            'companyName': 'Brain Johnston',
                            'fullName': 'Brain Johnston',
                        },
                    },
                },
                'content': {
                    'unitOfMeasurement': 'metric',
                    'isCustomsDeclarable': False,
                    'incoterm': 'DAP',
                    'description': 'Order from company 0',
                    'packages': [
                        {
                            'customerReferences': [{'value': 'Order from company 0', 'typeCode': 'CU'}],
                            'weight': 6.0,
                            'description': '',
                            'dimensions': {'length': 7.0, 'width': 10.0, 'height': 5.0},
                        },
                    ],
                },
            },
        }


class ExpressFreightOrderTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.company = CompanyFactory(
            dhl_account_code='123abc',
            shopify_domain='https://company.shopify.com',
            shopify_webhook_key='foo',
            shopify_api_key='bar',
            shopify_password='pass',
        )
        self.client = AuthenticatedClient(company=self.company)
        self.orders_url = reverse('orders-list')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    @mock.patch('SalsaVerde.orders.views.express_freight.session.request')
    def test_ef_form_submit(self, mock_ef, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        mock_ef.side_effect = fake_ef()
        r = self.client.get(reverse('fulfill-order-ef') + '?shopify_order=123')
        self.assertContains(r, 'Brain Johnston')
        form_data = {
            'name': 'Brain Johnston',
            'first_line': '123 Fake Street.',
            'town': 'Bel fast',
            'region': 'NORTH IRELAND',
            'county': 'CO. DOWN',
            'phone': '+123789',
            'shopify_order': '123',
            'dispatch_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'form-0-height': 5,
            'form-0-weight': 6,
            'form-0-length': 7,
            'form-0-width': 10,
            **empty_formset('form'),
        }
        r = self.client.post(reverse('fulfill-order-ef') + '?shopify_order=123', follow=True, data=form_data)
        self.assertRedirects(r, self.orders_url)
        self.assertContains(r, 'Order created')
        order = Order.objects.get()
        assert order.shopify_id == '123'
        assert order.shipping_id == 'EF_123'
        assert order.tracking_url == 'https://foobar.com/EF_123'
        assert order.labels.count() == 2
        assert order.company == self.company
        call_args = mock_ef.mock_calls[1][2]
        assert call_args == {
            'url': 'https://online.expressfreight.co.uk:10813/api/Consignment/CreateConsignment',
            'headers': {'Authorization': 'Bearer AuthToken'},
            'json': {
                'consigneeName': 'Brain Johnston',
                'ConsigneeNumber': '',
                'ConsigneeTownland': '',
                'SpecialInstructions': '',
                'consigneeStreet': '123 Fake Street',
                'consigneeStreet2': '',
                'consigneeCity': 'Bel fast',
                'consigneeCounty': 'CO. DOWN',
                'consigneePostcode': '',
                'contactName': 'Brain Johnston',
                'contactNo': '00123789',
                'orderReference': '123',
                'serviceType': 'STANDARD',
                'consigneeRegion': 'NORTH IRELAND',
                'dispatchDate': '2018-02-02',
                'labelsLink': False,
                'items': [
                    {
                        'itemType': 'CARTON',
                        'itemWeight': 6,
                        'itemHeight': 5,
                        'itemWidth': 10,
                        'itemLength': 7,
                        'dangerousGoods': False,
                        'limitedQuantities': False,
                    },
                ],
            },
        }

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    @mock.patch('SalsaVerde.orders.views.express_freight.session.request')
    def test_ef_form_submit_no_county(self, mock_ef, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        mock_ef.side_effect = fake_ef()
        r = self.client.get(reverse('fulfill-order-ef') + '?shopify_order=123')
        self.assertContains(r, 'Brain Johnston')
        form_data = {
            'name': 'Brain Johnston',
            'first_line': '123 Fake Street.',
            'town': 'Bel fast',
            'region': 'NORTH IRELAND',
            'phone': '+123789',
            'shopify_order': '123',
            'dispatch_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'form-0-height': 5,
            'form-0-weight': 6,
            'form-0-length': 7,
            'form-0-width': 10,
            **empty_formset('form'),
        }
        r = self.client.post(reverse('fulfill-order-ef') + '?shopify_order=123', follow=True, data=form_data)
        assert r.status_code == 200


class OrderTestCase(TestCase):
    def setUp(self):
        self.company = CompanyFactory(shopify_api_key='Foo', shopify_password='Bar')
        self.client = AuthenticatedClient(company=self.company)
        self.list_url = reverse('orders-list')

    def test_order_list(self):
        u = UserFactory(first_name='Cus', last_name='Tomer', company=self.company)
        order = OrderFactory(company=self.company, user=u)
        r = self.client.get(self.list_url)
        self.assertContains(r, 'Cus Tomer')
        self.assertContains(r, f'Order #{order.id}')
        self.assertContains(r, 'No shipping address added')

    def test_order_list_shopify_details(self):
        u = UserFactory(first_name='Cus', last_name='Tomer', company=self.company)
        order = OrderFactory(
            company=self.company,
            user=u,
            extra_data={'shipping_address': {'city': 'Portadown', 'country_code': 'GB'}, 'name': 123},
            shopify_id='123',
        )
        r = self.client.get(self.list_url)
        self.assertContains(r, 'Cus Tomer')
        self.assertContains(r, f'Order #{order.id} (123)')
        self.assertContains(r, 'Portadown, GB')

    def test_order_deets_unfulfilled(self):
        u = UserFactory(first_name='Cus', last_name='Tomer', company=self.company)
        order = OrderFactory(company=self.company, user=u)
        r = self.client.get(order.get_absolute_url())
        self.assertContains(r, 'Fulfill with', 2)
        self.assertNotContains(r, 'Update Product Batch Codes')
        self.assertNotContains(r, 'View in Shopify')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_shopify_deets_unfulfilled(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        order = OrderFactory(company=self.company, shopify_id=123)
        r = self.client.get(order.get_absolute_url())
        self.assertContains(r, 'Fulfill with', 2)
        self.assertContains(r, 'View in Shopify')
        self.assertNotContains(r, 'Update Product Batch Codes')
        self.assertNotContains(r, 'Tracking')

    def test_order_deets_fulfilled(self):
        order = OrderFactory(company=self.company, status=Order.STATUS_FULFILLED)
        r = self.client.get(order.get_absolute_url())
        self.assertNotContains(r, 'Fulfill with')
        self.assertContains(r, 'Update Product Batch Codes')
        self.assertNotContains(r, 'Shipping label')

    def test_order_fulfilled_has_label(self):
        u = UserFactory(first_name='Cus', last_name='Tomer', company=self.company)
        order = OrderFactory(company=self.company, user=u, status=Order.STATUS_FULFILLED, tracking_url=None)
        doc = Document.objects.create(order=order, author=self.client.user)
        doc.file.save('shipping_label.pdf', ContentFile('test'), save=True)

        r = self.client.get(order.get_absolute_url())
        self.assertNotContains(r, 'Fulfill with')
        self.assertContains(r, 'Update Product Batch Codes')
        self.assertContains(r, 'Shipping Label')

    def test_order_fulfilled_has_tracking(self):
        u = UserFactory(first_name='Cus', last_name='Tomer', company=self.company)
        order = OrderFactory(company=self.company, user=u, status=Order.STATUS_FULFILLED, tracking_url='https://g.com')

        r = self.client.get(order.get_absolute_url())
        self.assertNotContains(r, 'Fulfill with')
        self.assertContains(r, 'Update Product Batch Codes')
        self.assertContains(r, 'Tracking')
        self.assertContains(r, 'https://g.com')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_shopify_deets_fulfilled(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        u = UserFactory(first_name='Cus', last_name='Tomer', company=self.company)
        order = OrderFactory(company=self.company, user=u, status=Order.STATUS_FULFILLED, shopify_id=123)
        r = self.client.get(order.get_absolute_url())
        self.assertNotContains(r, 'Fulfill with')
        self.assertContains(r, 'View in Shopify')
        self.assertContains(r, 'Products ordered')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_add_product_batch_codes(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        order = OrderFactory(company=self.company, shopify_id=456)
        r = self.client.get(reverse('order-packed-product', args=[order.id]))
        self.assertContains(r, 'Bramley apple')
        p1 = ProductFactory(product_type__company=self.company, product_type__name='Foo')
        p2 = ProductFactory(product_type__company=self.company, product_type__name='Bar')
        formset_data = empty_formset('form')
        formset_data['form-TOTAL_FORMS'] = 2
        form_data = {
            'form-0-product': p1.id,
            'form-0-quantity': 2,
            'form-1-product': p2.id,
            'form-1-quantity': 3,
            **formset_data,
        }
        r = self.client.post(reverse('order-packed-product', args=[order.id]), follow=True, data=form_data)
        self.assertRedirects(r, order.get_absolute_url())
        order = Order.objects.get()
        assert order.products.count() == 2
        assert sum(order.products.values_list('quantity', flat=True)) == 5
        self.assertContains(r, 'Foo')
        self.assertContains(r, 'Bar')

        # Now delete one
        form_data = {
            'form-0-product': p1.id,
            'form-0-quantity': 0,
            'form-1-product': p2.id,
            'form-1-quantity': 1,
            **formset_data,
        }
        r = self.client.post(reverse('order-packed-product', args=[order.id]), follow=True, data=form_data)
        self.assertRedirects(r, order.get_absolute_url())
        order = Order.objects.get()
        assert order.products.count() == 1
        self.assertNotContains(r, 'Foo')
        self.assertContains(r, 'Bar')

    def test_remove_null_vals(self):
        from SalsaVerde.orders.views.dhl import remove_null_vals

        data = {
            '1': None,
            '2': 'Foo',
            '3': {'a': None, 'b': 'Bar', 'c': {'i': None, 'ii': 'Foobar', 'iii': [{'x': None, 'y': 'BarFoo'}]}},
        }
        assert remove_null_vals(data) == {
            '2': 'Foo',
            '3': {'b': 'Bar', 'c': {'ii': 'Foobar', 'iii': [{'y': 'BarFoo'}]}},
        }
