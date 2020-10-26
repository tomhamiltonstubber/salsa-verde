from dateutil.relativedelta import relativedelta
from django.core.management import BaseCommand
from django.utils.timezone import now

from SalsaVerde.company.models import Company
from SalsaVerde.orders.shopify import process_order_event
from SalsaVerde.orders.views.shopify import shopify_request


class Command(BaseCommand):
    help = 'Recreates database schema and populates it with fake data'

    def handle(self, *args, **options):
        args = {
            'created_at_max': now().date() - relativedelta(weeks=4),
            'limit': 250,
            'status': 'any',
            'fields': 'id,app_id',
            'fulfillment_status': 'all',
        }
        for company in Company.objects.filter(shopify_password__isnull=False):
            success, orders = shopify_request('orders.json?', data=args, company=company)
            assert success
            for order in orders['orders']:
                process_order_event('orders/create', order, company=company)
