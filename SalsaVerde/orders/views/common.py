from collections import Counter
from datetime import datetime
from operator import itemgetter

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from SalsaVerde.orders.forms.common import PackageFormSet
from SalsaVerde.orders.models import Order
from SalsaVerde.orders.views.shopify import (
    ShopifyHelperMixin,
    get_shopify_order,
    get_shopify_orders,
    shopify_fulfill_order,
)
from SalsaVerde.stock.views.base_views import DetailView, DisplayHelpers, SVFormView


class CreateShipmentError(Exception):
    pass


class CreateOrderView(ShopifyHelperMixin, SVFormView, TemplateView):
    title = 'Create shipping order'
    order_data = None

    def dispatch(self, request, *args, **kwargs):
        self.shopify_order_id = request.GET.get('shopify_order')
        if self.shopify_order_id:
            success, self.order_data = get_shopify_order(self.shopify_order_id)
            if not success:
                messages.error(request, 'Error getting data from shopify: %s' % self.order_data)
                return reverse('orders-list')
            elif self.order_data.get('fulfillment_status') == 'fulfilled':
                messages.error(request, 'Order already fulfilled: %s' % self.order_data)
                return reverse('orders-list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.shopify_order_id:
            kwargs['order_id'] = self.shopify_order_id
            if not self.request.POST:
                kwargs.update(shopify_data=self.order_data['order'])
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            package_formset = PackageFormSet(self.request.POST)
        else:
            package_formset = PackageFormSet()
        ctx['package_formset'] = package_formset
        if self.shopify_order_id:
            _, order_data = get_shopify_order(self.shopify_order_id)
            ctx['order_data'] = order_data
        return ctx

    def create_shipment(self, form, package_form):
        raise NotImplementedError

    def form_valid(self, form):
        formset = PackageFormSet(self.request.POST)
        formset.full_clean()
        if not formset.is_valid():
            return self.form_invalid(form)
        try:
            order = self.create_shipment(form, formset)
        except CreateShipmentError:
            return super().form_invalid(form)
        else:
            if self.shopify_order_id:
                success, r = shopify_fulfill_order(order)
                if success:
                    messages.success(self.request, 'Order fulfilled')
                    order.fulfilled = True
                    order.save()
                else:
                    messages.error(self.request, 'Error fulfilling Shopify order: %s' % r.content.decode())
                    return super().form_invalid(form)
        return redirect(reverse('orders-list'))


class OrdersList(ShopifyHelperMixin, DisplayHelpers, TemplateView):
    template_name = 'order_list.jinja'
    title = 'Orders'

    def get_button_menu(self):
        if self.request.GET.get('fulfilled'):
            yield {'name': 'Back to open orders', 'url': reverse('orders-list')}
        else:
            yield {'name': 'View fulfilled orders', 'url': reverse('orders-list') + '?fulfilled=true'}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.GET.get('fulfilled'):
            _, data = get_shopify_orders('shipped')
        else:
            _, data = get_shopify_orders('unfulfilled')
        order_lu = {o.shopify_id: o for o in Order.objects.request_qs(self.request).filter(fulfilled=False)}
        for order in data['orders']:
            order['order_obj'] = order_lu.get(str(order['id']))
        ctx['orders'] = sorted(data['orders'], key=itemgetter('created_at'), reverse=True)
        return ctx

    def get_location(self, order):
        shipping_address = order['shipping_address']
        return f"{shipping_address['city']}, {shipping_address['country_code']}"

    def created_at(self, dt):
        return datetime.fromisoformat(dt).strftime(settings.DATE_FORMAT)


orders_list = OrdersList.as_view()


class OrderDetails(ShopifyHelperMixin, DetailView):
    template_name = 'order_view.jinja'
    model = Order
    object: Order
    title = 'Order'

    def get_queryset(self):
        return super().get_queryset().select_related('products')

    def get_button_menu(self):
        yield {'name': 'Back', 'url': reverse('orders-list') + '?fulfilled=true'}
        if self.object.shopify_id:
            yield {'name': 'View in Shopify', 'url': self.get_shopify_url(self.object.shopify_id), 'newtab': True}
        for i, label in enumerate(self.object.label_urls):
            yield {'name': f'Label {i + 1}', 'url': label, 'newtab': True, 'icon': 'fa-shopping-basket'}
        if self.object.tracking_url:
            yield {'name': 'Tracking', 'url': self.object.tracking_url, 'newtab': True}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if shopify_order := self.object.shopify_id:
            _, order_data = get_shopify_order(shopify_order)
            ctx.update(order_data=order_data['order'])
        ctx['products'] = Counter(self.object.products.select_related('product_type'))
        return ctx


order_details = OrderDetails.as_view()


class ShopifyOrderView(ShopifyHelperMixin, DisplayHelpers, TemplateView):
    template_name = 'order_view.jinja'
    title = 'Order'

    def get_button_menu(self):
        yield {'name': 'Back', 'url': reverse('orders-list')}
        yield {
            'name': 'View in Shopify',
            'url': self.get_shopify_url(self.shopify_id),
            'newtab': True,
            'icon': 'fa-shopping-basket',
        }
        yield {
            'name': 'Fulfill with ExpressFreight',
            'url': reverse('fulfill-order-ef') + f'?shopify_order={self.shopify_id}',
            'icon': 'fa-truck',
        }

    def dispatch(self, request, *args, **kwargs):
        self.shopify_id = kwargs['id']
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        _, order_data = get_shopify_order(self.shopify_id)
        return super().get_context_data(order_data=order_data['order'])


shopify_order_details = ShopifyOrderView.as_view()
