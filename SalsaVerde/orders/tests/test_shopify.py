import hashlib
import hmac
import json
from unittest import mock

from django.test import Client, TestCase
from django.urls import reverse
from django.utils.text import slugify

from SalsaVerde.company.models import User
from SalsaVerde.orders.models import Order
from SalsaVerde.orders.tests.mock_objs import fake_shopify
from SalsaVerde.stock.factories.company import CompanyFactory
from SalsaVerde.stock.factories.users import UserFactory


class ShopifyWebhookTestCase(TestCase):
    def setUp(self):
        self.company = CompanyFactory(
            shopify_webhook_key='WEB_TEST',
            shopify_domain='https://foo.shopify.com',
            shopify_api_key='Fookey',
            shopify_password='Foopass',
            name='Salsa Verde',
        )
        self.admin = UserFactory(company=self.company)
        self.callback_url = reverse('shopify-callback')

    # def test_callback_wrong_sig(self):
    #     sig = hmac.new(
    #         self.company.shopify_webhook_key.encode(), json.dumps({'a': '2'}).encode(), hashlib.sha256
    #     ).digest()
    #     r = Client().post(
    #         self.callback_url,
    #         data={'foo': 'bar'},
    #         HTTP_X_SHOPIFY_SHOP_DOMAIN='https://foo.shopify.com',
    #         HTTP_X_SHOPIFY_HMAC_SHA256=sig,
    #     )
    #     assert r.status_code == 403
    #     r = Client().post(
    #         self.callback_url,
    #         data={'foo': 'bar'},
    #         HTTP_X_SHOPIFY_SHOP_DOMAIN='https://foo.shopify.com',
    #         HTTP_X_SHOPIFY_HMAC_SHA256='FOOBAR',
    #     )
    #     assert r.status_code == 403

    def test_callback_company_doesnt_exist(self):
        r = Client().post(
            self.callback_url,
            data={'foo': 'bar'},
            HTTP_X_SHOPIFY_SHOP_DOMAIN='https://Z.com',
            HTTP_X_SHOPIFY_HMAC_SHA256='FooSig',
        )
        assert r.status_code == 299

    def callback_request(self, data, event):
        sig = hmac.new(self.company.shopify_webhook_key.encode(), json.dumps(data).encode(), hashlib.sha256).digest()
        return Client().post(
            self.callback_url,
            data=data,
            HTTP_X_SHOPIFY_SHOP_DOMAIN=self.company.shopify_domain,
            HTTP_X_SHOPIFY_HMAC_SHA256=sig,
            HTTP_X_SHOPIFY_TOPIC=event,
        )

    @mock.patch('SalsaVerde.orders.views.shopify.logger.info')
    def test_callback_unknown_event(self, mock_logger):
        r = self.callback_request({'Foo': 'Bar'}, 'unknown/event')
        assert r.status_code == 220
        mock_logger.assert_called_with('Shopify event status %s:%s', 220, 'Unknown event unknown/event')

    @mock.patch('SalsaVerde.orders.views.shopify.logger.info')
    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_created_new_user(self, mock_shopify, mock_logger):
        mock_shopify.side_effect = fake_shopify()
        r = self.callback_request({'id': '123'}, 'orders/create')
        assert r.status_code == 210
        order = Order.objects.get()
        assert order.shopify_id == '123'
        assert order.company == self.company
        user = User.objects.exclude(id=self.admin.id).get()
        assert user.get_full_name() == 'Brain Johnston'
        assert not user.administrator
        assert user.email == 'brain_johnston@fakemail.com'
        mock_logger.assert_called_with('Shopify event status %s:%s', 210, 'Order created')
        assert not user.has_usable_password()
        assert order.user == user
        assert order.status == Order.STATUS_UNFULFILLED
        order.extra_data.pop('created_at')
        assert order.extra_data == {
            'id': '123',
            'name': '#123',
            'customer': {
                'email': 'brain_johnston@fakemail.com',
                'last_name': 'Johnston',
                'first_name': 'Brain',
            },
            'line_items': [
                {
                    'name': 'Bramley apple infused Balsamic Vinegar - 250ml',
                    'price': '9.00',
                    'quantity': 5,
                },
            ],
            'total_price': '40.50',
            'billing_address': {
                'zip': 'BT72 2LL',
                'city': 'Belfast',
                'name': 'Brain Johnston',
                'phone': '07714 123456',
                'country': 'United Kingdom',
                'address1': '123 Fake st',
                'address2': '',
                'province': None,
                'country_code': 'GB',
            },
            'total_discounts': '4.50',
            'shipping_address': {
                'zip': 'BT72 2LL',
                'city': 'Belfast',
                'name': 'Brain Johnston',
                'phone': '07714 123456',
                'country': 'United Kingdom',
                'address1': '123 Fake st',
                'address2': '',
                'province': None,
                'country_code': 'GB',
            },
            'fulfillment_status': None,
            'total_line_items_price': '45.00',
        }

    @mock.patch('SalsaVerde.orders.shopify.logger.info')
    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_created_fulfilled_new_user_no_email(self, mock_shopify, mock_logger):
        mock_shopify.side_effect = fake_shopify()
        r = self.callback_request({'id': '456'}, 'orders/create')
        assert r.status_code == 210
        order = Order.objects.get()
        assert order.shopify_id == '456'
        assert order.company == self.company
        user = User.objects.exclude(id=self.admin.id).get()
        assert user.get_full_name() == 'Tom Jones'
        assert not user.administrator
        assert user.email == 'tom_jones@inactive.salsa-verde.com'
        calls = [c[0] for c in mock_logger.call_args_list]
        assert calls[1] == ('Updated order %s with shopify data', order.id)
        assert not user.has_usable_password()
        assert order.user == user
        assert order.status == Order.STATUS_FULFILLED

    @mock.patch('SalsaVerde.orders.views.shopify.logger.info')
    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_update_order(self, mock_shopify, mock_logger):
        mock_shopify.side_effect = fake_shopify()
        user = UserFactory(company=self.company, administrator=False)

        order = Order.objects.create(company=self.company, shopify_id='456', user=user, status=Order.STATUS_UNFULFILLED)
        r = self.callback_request({'id': '456'}, 'orders/create')
        assert r.status_code == 210
        order = Order.objects.get(id=order.id)
        assert order.shopify_id == '456'
        assert order.user == user
        assert order.status == Order.STATUS_FULFILLED
        mock_logger.assert_called_with('Shopify event status %s:%s', 210, 'Order updated')

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_create_order_multiple_orders(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        Order.objects.create(company=self.company, shopify_id='456', status=Order.STATUS_UNFULFILLED)
        Order.objects.create(company=self.company, shopify_id='456', status=Order.STATUS_UNFULFILLED)
        r = self.callback_request({'id': '456'}, 'orders/updated')
        assert r.status_code == 210

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_created_no_user(self, mock_shopify):
        _fake_shopify = fake_shopify()
        _fake_shopify.orders[0].pop('customer')
        mock_shopify.side_effect = _fake_shopify

        order = Order.objects.create(company=self.company, shopify_id='123', status=Order.STATUS_UNFULFILLED)
        r = self.callback_request({'id': '123'}, 'orders/create')
        assert r.status_code == 210
        order = Order.objects.get(id=order.id)
        assert order.shopify_id == '123'
        assert not order.user
        assert not User.objects.filter(administrator=False).exists()

    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_created_update_user(self, mock_shopify):
        mock_shopify.side_effect = fake_shopify()
        user = UserFactory(
            company=self.company,
            administrator=False,
            last_name='Johnston',
            first_name='brain',
            email=f'foo_bar@inactive.{slugify(self.company.name)}.com',
        )
        order = Order.objects.create(company=self.company, shopify_id='123', status=Order.STATUS_UNFULFILLED)
        r = self.callback_request({'id': '123'}, 'orders/create')
        assert r.status_code == 210
        order = Order.objects.get(id=order.id)
        assert order.shopify_id == '123'
        assert order.user == user
        assert order.user.email == 'brain_johnston@fakemail.com'

    @mock.patch('SalsaVerde.orders.views.shopify.logger.info')
    @mock.patch('SalsaVerde.orders.views.shopify.session.request')
    def test_order_cancelled(self, mock_shopify, mock_logger):
        mock_shopify.side_effect = fake_shopify()
        user = UserFactory(company=self.company, administrator=False)

        order = Order.objects.create(company=self.company, shopify_id='123', user=user, status=Order.STATUS_UNFULFILLED)
        r = self.callback_request({'id': '123'}, 'orders/cancelled')
        assert r.status_code == 211
        order = Order.objects.get(id=order.id)
        assert order.shopify_id == '123'
        assert order.user == user
        assert order.status == Order.STATUS_CANCELLED
        mock_logger.assert_called_with('Shopify event status %s:%s', 211, 'Order deleted')
