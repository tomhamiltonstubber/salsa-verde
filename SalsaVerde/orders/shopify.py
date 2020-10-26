from datetime import datetime

from django_rq import job

from SalsaVerde.company.models import Company
from SalsaVerde.orders.models import Order
from SalsaVerde.orders.views.shopify import logger, shopify_request, get_shopify_order


@job
def shopify_fulfill_order(order: Order):
    # Location is hard coded here as it doesn't change
    assert order.shopify_id
    data = {
        'fulfillment': {
            'location_id': 5032451,
            'tracking_number': order.shipping_id,
            'tracking_urls': [order.tracking_url],
            'notify_customer': True,
        }
    }
    success, content = shopify_request(
        f'orders/{order.shopify_id}/fulfillments.json', method='POST', data=data, company=order.company
    )
    if success:
        order.status = Order.STATUS_FULFILLED
        order.save()
    else:
        logger.error('Error fulfilling Shopify order: %s', content)


@job
def update_order_details(pk, company_id):
    order = Order.objects.get(id=pk, company_id=company_id)
    assert order.shopify_id
    _, order_data = get_shopify_order(order.shopify_id, company=order.company)
    order_data = order_data['order']
    if order.status == Order.STATUS_UNFULFILLED and order_data['fulfillment_status'] == 'fulfilled':
        order.status = Order.STATUS_FULFILLED
        order.save(update_fields=['status'])
    if order_data != order.extra_data:
        logger.info('Updated order %s with shopify data', order.id)
        Order.objects.filter(id=order.id).update(
            extra_data=order_data, created=datetime.fromisoformat(order_data['created_at'])
        )


def process_order_event(topic, event_data, company: Company):
    obj, event = topic.split('/')
    msg = f'Unknown event {topic}'
    status = 220
    if obj == 'orders':
        if event in {'create', 'updated', 'paid', 'fulfilled'}:
            try:
                order, created = Order.objects.get_or_create(shopify_id=event_data['id'], company=company)
            except Order.MultipleObjectsReturned:
                order, created = Order.objects.filter(shopify_id=event_data['id'], company=company).first(), True
            msg = 'Order created' if created else 'Order already exists'
            status = 210
            update_order_details.delay(order.id, company.id)
        elif event in {'cancelled', 'delete'}:
            Order.objects.filter(shopify_id=event_data['id']).update(status=Order.STATUS_CANCELLED)
            msg = 'Order deleted'
            status = 211
    return msg, status
