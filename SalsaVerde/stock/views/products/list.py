from django.urls import reverse

from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.models import Product


class ProductList(ModelListView):
    model = Product
    display_items = [
        'product_type',
        'date_of_infusion',
        'date_of_bottling',
        'date_of_best_before',
        'yield_quantity',
    ]
    order_by = '-date_of_bottling'
    icon = 'fa-bottle-droplet'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.view_finished = bool(self.request.GET.get('finished'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().select_related('product_type').filter(finished=self.view_finished)

    def get_button_menu(self):
        yield {'name': 'Record new product infusion', 'url': reverse('products-add')}
        if self.view_finished:
            yield {'name': 'View Current Products', 'url': reverse('products')}
        else:
            yield {'name': 'View Finished Products', 'url': reverse('products') + '?finished=true'}


product_list = ProductList.as_view()
