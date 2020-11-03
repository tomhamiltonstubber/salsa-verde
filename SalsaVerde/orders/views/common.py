from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from SalsaVerde.common.views import DetailView, ListView, SVFormView, UpdateModelView
from SalsaVerde.orders.forms.common import PackageFormSet, PackedProductFormSet
from SalsaVerde.orders.models import Order, PackageTemplate, ProductOrder
from SalsaVerde.orders.shopify import shopify_fulfill_order
from SalsaVerde.orders.views.shopify import ShopifyHelperMixin, get_shopify_order


class CreateShipmentError(Exception):
    pass


class CreateOrderView(ShopifyHelperMixin, SVFormView, TemplateView):
    title = 'Create shipping order'
    order_data = None

    def dispatch(self, request, *args, **kwargs):
        self.shopify_order_id = request.GET.get('shopify_order')
        if self.shopify_order_id:
            success, self.order_data = get_shopify_order(self.shopify_order_id, company=request.user.company)
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
        ctx.update(
            package_formset=package_formset,
            pack_temp_lu={
                str(p.id): {k: float(getattr(p, k, 0)) for k in ['width', 'height', 'length', 'weight']}
                for p in PackageTemplate.objects.request_qs(self.request)
            },
        )
        if self.shopify_order_id:
            _, order_data = get_shopify_order(self.shopify_order_id, company=self.request.user.company)
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
                shopify_fulfill_order.delay(order)
                messages.success(self.request, 'Fulfilling order')
        return redirect(reverse('orders-list'))


class OrdersList(ShopifyHelperMixin, ListView):
    title = 'Orders'
    model = Order
    display_items = [
        ('Order', 'func|order_name'),
        'created',
        ('Customer', 'func|billing_name'),
        ('Total', 'func|total'),
        ('Status', 'get_status_display'),
        ('Location', 'func|get_location'),
    ]

    def get_button_menu(self):
        return []

    def order_name(self, obj):
        n = f'Order #{obj.id}'
        if obj.shopify_id:
            n += f' ({obj.extra_data.get("name")})'
        return mark_safe(f'<a href="{obj.get_absolute_url()}">{n}</a>')

    def billing_name(self, obj):
        return obj.user.get_full_name() if obj.user else '—'

    def total(self, obj):
        return f'£{obj.extra_data.get("total_price")}'

    def get_location(self, obj):
        if shipping_address := obj.extra_data.get('shipping_address'):
            return f"{shipping_address['city']}, {shipping_address['country_code']}"
        return 'No shipping address added'


orders_list = OrdersList.as_view()


class OrderDetails(ShopifyHelperMixin, DetailView):
    template_name = 'order_view.jinja'
    model = Order
    title = 'Order'

    def get_queryset(self):
        return super().get_queryset().select_related('products')

    def get_button_menu(self):
        yield {'name': 'Back', 'url': reverse('orders-list')}
        if self.object.shopify_id:
            yield {
                'name': 'View in Shopify',
                'url': self.get_shopify_url(self.object.shopify_id),
                'newtab': True,
                'icon': 'fa-shopping-basket',
            }
        if self.object.status == Order.STATUS_UNFULFILLED:
            yield {
                'name': 'Fulfill with ExpressFreight',
                'url': reverse('fulfill-order-ef') + f'?shopify_order={self.object.shopify_id}',
                'icon': 'fa-truck',
            }
            yield {
                'name': 'Fulfill with DHL',
                'url': reverse('fulfill-order-dhl') + f'?shopify_order={self.object.shopify_id}',
                'icon': 'fa-truck',
            }
        else:
            yield {
                'name': 'Update Product Batch Codes',
                'url': reverse('order-packed-product', kwargs={'pk': self.object.pk}),
            }
            if self.object.tracking_url:
                yield {'name': 'Tracking', 'url': self.object.tracking_url, 'newtab': True}
            for i, label in enumerate(self.object.labels.all()):
                yield {'name': f'Shipping Label {i + 1}', 'url': label.file.url, 'newtab': True}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if shopify_order := self.object.shopify_id:
            _, order_data = get_shopify_order(shopify_order, company=self.request.user.company)
            ctx.update(order_data=order_data['order'])
        return ctx


order_details = OrderDetails.as_view()


class OrderUpdatePackedProduct(ShopifyHelperMixin, UpdateModelView):
    form_class = PackedProductFormSet
    title = 'Record product'
    template_name = 'packed_product_form.jinja'
    model = Order

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.pop('instance')
        return form_kwargs

    def get_initial(self):
        return [
            {'product': po.product, 'quantity': po.quantity}
            for po in self.object.products.select_related('product', 'product__product_type')
        ]

    def form_valid(self, formset):
        self.object.products.all().delete()
        for form in formset.forms:
            cd = form.cleaned_data
            if cd.get('quantity'):
                ProductOrder.objects.create(order=self.object, product=cd['product'], quantity=cd['quantity'])
        return redirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.shopify_id:
            _, order_data = get_shopify_order(self.object.shopify_id, company=self.request.user.company)
            ctx['order_data'] = order_data['order']
        ctx['formset'] = ctx.pop('form')
        if self.object.products.exists():
            del ctx['formset'].forms[-1]
        return ctx


update_packed_product = OrderUpdatePackedProduct.as_view()
