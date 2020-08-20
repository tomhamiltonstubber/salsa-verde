import factory

from SalsaVerde.orders.models import Order
from SalsaVerde.stock.factories.company import CompanyFactory


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    shipping_id = 'test_123'
    tracking_url = 'https://example.com/tracking'
    company = factory.SubFactory(CompanyFactory)
    label_urls = ['https://example.com/label_1']
