import logging
import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from SalsaVerde.orders.forms.dhl import DHLLabelForm
from SalsaVerde.orders.views.shopify import shopify_fulfill_order, shopify_request
from SalsaVerde.stock.views.base_views import SVFormView

session = requests.Session()
logger = logging.getLogger('salsa-verde.orders')


def dhl_request(url, data=None, method='GET'):
    logger.info(f'Making request to DHL {url}')
    url = f'{settings.DHL_BASE_URL}/{url}'
    data = data or {}
    if method == 'GET':
        r = session.request(method, url, auth=(settings.DHL_API_KEY, settings.DHL_PASSWORD))
    else:
        r = session.request(method, url, auth=(settings.DHL_API_KEY, settings.DHL_PASSWORD), json=data)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        logger.warning('Request to DHL failed: %r', r.content.decode())
        return False, r.content.decode()
    return True, r.json()


class DHLLabelCreate(SVFormView, TemplateView):
    template_name = 'dhl_order_form.jinja'
    form_class = DHLLabelForm
    title = 'Create shipping order'

    def get(self, request, *args, **kwargs):
        _, self.order_data = shopify_request(f'orders/{self.order_id}.json')
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.order_id = kwargs['order_id']
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order_id'] = self.order_id
        if not self.request.POST:
            kwargs.update(shopify_data=self.order_data['order'])
        return kwargs

    def form_valid(self, form):
        data = form.ef_form_data()
        messages.success(self.request, 'Order created')
        shopify_fulfill_order(self.order_id)
        return redirect(reverse('shopify-orders'))


dhl_label_create = DHLLabelCreate.as_view()
