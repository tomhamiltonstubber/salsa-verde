from django.urls import reverse

from SalsaVerde.common.views import DetailView
from SalsaVerde.stock.models import ProductType


class ProductTypeDetails(DetailView):
    model = ProductType
    display_items = [
        'ingredient_types',
        'code',
    ]

    def extra_display_items(self):
        return [
            {
                'title': 'Sizes',
                'qs': self.object.product_type_sizes.all(),
                'fields': ['size', 'sku_code', 'bar_code'],
                'add_url': reverse('product-type-sizes-add', kwargs={'product_type': self.object.pk}),
            }
        ]


product_type_details = ProductTypeDetails.as_view()
