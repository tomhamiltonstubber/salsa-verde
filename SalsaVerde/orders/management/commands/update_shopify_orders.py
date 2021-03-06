from dateutil.relativedelta import relativedelta
from django.core.management import BaseCommand
from django.utils.timezone import now

from SalsaVerde.company.models import Company
from SalsaVerde.orders.shopify import process_shopify_event
from SalsaVerde.orders.views.shopify import shopify_request


class Command(BaseCommand):
    help = 'Recreates database schema and populates it with fake data'

    def handle(self, *args, **options):
        args = {
            'limit': 250,
            'status': 'any',
            'fields': 'id,app_id',
            'fulfillment_status': 'all',
        }
        url_kwargs = {'created_at_min': now().date() - relativedelta(weeks=1), **args}
        for company in Company.objects.filter(shopify_password__isnull=False):
            success, orders = shopify_request('orders.json?', data=url_kwargs, company=company)
            assert success, orders
            for order in orders['orders']:
                process_shopify_event('orders/create', order, company=company)
