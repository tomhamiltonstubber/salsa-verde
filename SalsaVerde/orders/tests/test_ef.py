from datetime import datetime
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from unittest import mock

from SalsaVerde.orders.models import Order
from SalsaVerde.orders.tests.mock_objs import fake_ef, fake_shopify
from SalsaVerde.stock.factories.company import CompanyFactory
from SalsaVerde.stock.tests.test_common import AuthenticatedClient, empty_formset


class ExpressFreightOrderTestCase(TestCase):
    def setUp(self):
        self.company = CompanyFactory()
        self.client = AuthenticatedClient(company=self.company)
        self.orders_url = reverse('shopify-orders')

    def test_manual_order(self):
        pass

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
            'first_line': '123 Fake Street',
            'town': 'Belfast',
            'region': 'NORTH IRELAND',
            'county': 'CO. DOWN',
            'phone': 123789,
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

    def test_submit_1_item(self):
        pass
