from datetime import datetime

from django_rq import job

from SalsaVerde.company.models import Company, User
from SalsaVerde.orders.models import Order
from SalsaVerde.orders.views.shopify import get_shopify_order, logger, shopify_request


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


def get_or_create_user(order_data: dict, company: Company):
    user = None
    if not (user_details := order_data.get('customer')):
        return
    if email := user_details.get('email'):
        user = User.objects.filter(company=company, email__iexact=email, administrator=False).first()
    if not user:
        user = User.objects.filter(
            company=company,
            last_name__iexact=user_details['last_name'],
            first_name__iexact=user_details['first_name'],
        ).first()
    inactive_email_ending = f"{user_details['last_name']}@inactive.{company.website}"
    if not user:
        email = (email or f"{user_details['first_name']}_{inactive_email_ending}").lower()
        user = User.objects.create(
            email=email, first_name=user_details['first_name'].title(), last_name=user_details['first_name'].title()
        )
        user.set_unusable_password()
        user.save()
    elif user.email.endswith(inactive_email_ending) and email:
        user.email = email
        user.save(update_fields=['email'])
    return user


@job
def update_order_details(pk, company_id):
    order = Order.objects.get(id=pk, company_id=company_id)
    assert order.shopify_id
    _, order_data = get_shopify_order(order.shopify_id, company=order.company)
    order_data = order_data['order']
    if not order.user:
        order.user = get_or_create_user(order_data, order.company)
        order.save(update_fields=['user'])
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
