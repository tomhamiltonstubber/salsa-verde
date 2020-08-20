from datetime import datetime
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from SalsaVerde.orders.factories.orders import OrderFactory
from SalsaVerde.orders.models import Order
from SalsaVerde.orders.tests.mock_objs import fake_ef, fake_shopify
from SalsaVerde.stock.factories.company import CompanyFactory
from SalsaVerde.stock.factories.product import ProductFactory
from SalsaVerde.stock.tests.test_common import AuthenticatedClient, empty_formset


class ExpressFreightOrderTestCase(TestCase):
    def setUp(self):
        self.company = CompanyFactory()
        self.client = AuthenticatedClient(company=self.company)
        self.orders_url = reverse('orders-list')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    @mock.patch('SalsaVerde.orders.views.express_freight.session.request')
    def test_form_submit(self, mock_ef, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        mock_ef.side_effect = fake_ef()
        r = self.client.get(reverse('fulfill-order-ef') + '?shopify_order=123')
        self.assertContains(r, 'Brain Johnston')
        self.assertContains(r, '<option value="NORTH IRELAND" selected>NI</option>')
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
        assert order.label_urls == ['https://foobar.com/EF_123_L1', 'https://foobar.com/EF_123_L2']
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
                'labelsLink': True,
                'items': [
                    {
                        'itemType': 'OTHER',
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


class OrderTestCase(TestCase):
    def setUp(self):
        self.company = CompanyFactory()
        self.client = AuthenticatedClient(company=self.company)

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_list_view(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        r = self.client.get(reverse('orders-list'))
        self.assertContains(r, '#123')
        self.assertNotContains(r, '#456')
        self.assertContains(r, reverse('order-details-shopify', args=[123]))

        r = self.client.get(reverse('orders-list') + '?fulfilled=true')
        self.assertNotContains(r, '#123')
        self.assertContains(r, '#456')
        self.assertContains(r, reverse('order-details-shopify', args=[456]))

        order = OrderFactory(company=self.company, shopify_id=456)
        r = self.client.get(reverse('orders-list') + '?fulfilled=true')
        self.assertContains(r, reverse('order-details', args=[order.id]))
        self.assertNotContains(r, reverse('order-details-shopify', args=[456]))

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_detail_view(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        order = OrderFactory(company=self.company, shopify_id=456)
        r = self.client.get(reverse('order-details', args=[order.id]))
        self.assertContains(r, 'Bramley apple')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_detail_view_shopify(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        r = self.client.get(reverse('order-details-shopify', args=[123]))
        self.assertContains(r, 'Bramley apple')

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
