from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from SalsaVerde.orders.forms.common import PackageFormSet
from SalsaVerde.orders.views.shopify import ShopifyHelperMixin, get_shopify_order, shopify_fulfill_order
from SalsaVerde.stock.views.base_views import SVFormView


class CreateShipmentError(Exception):
    pass


class CreateOrderView(ShopifyHelperMixin, SVFormView, TemplateView):
    title = 'Create shipping order'

    def dispatch(self, request, *args, **kwargs):
        self.shopify_order_id = request.GET.get('shopify_order')
        if self.shopify_order_id:
            success, self.order_data = get_shopify_order(self.shopify_order_id)
            if not success:
                messages.error(request, 'Error getting data from shopify: %s' % self.order_data)
                return reverse('shopify-orders')
            elif self.order_data.get('fulfillment_status') == 'fulfilled':
                messages.error(request, 'Order already fulfilled: %s' % self.order_data)
                return reverse('shopify-orders')
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
                else:
                    messages.error(self.request, 'Error fulfilling Shopify order: %s' % r.content.decode())
                    return super().form_invalid(form)
        return redirect(reverse('shopify-orders'))
