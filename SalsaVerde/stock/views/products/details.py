import textwrap

from django.urls import reverse

from SalsaVerde.common.views import DetailView
from SalsaVerde.stock.models import Product


class ProductDetails(DetailView):
    model = Product

    def get_title(self):
        return textwrap.shorten(self.object.product_type.name, width=35, placeholder='…') + self.object.batch_code

    def get_display_items(self):
        items = [
            'product_type',
            'date_of_infusion',
            'batch_code',
            ('Stage', 'get_status_display'),
        ]
        if self.object.status == Product.STATUS_BOTTLED:
            items += [
                'date_of_best_before',
                'yield_quantity',
                'best_before_applied',
                'quality_check_successful',
                'batch_code_applied',
            ]
        return items

    def get_button_menu(self):
        btns = list(super().get_button_menu())
        if self.object.finished:
            label = 'Mark as In stock'
        else:
            label = 'Mark as Finished'
        btns.append(
            {
                'name': label,
                'url': reverse('product-status', kwargs={'pk': self.object.pk}),
                'method': 'POST',
                'group': 2,
                'icon': 'fa-check',
            }
        )
        return btns

    def extra_display_items(self):
        return [
            {
                'title': 'Ingredients',
                'qs': self.object.product_ingredients.select_related('ingredient__ingredient_type'),
                'fields': [('Name', 'ingredient__ingredient_type'), 'ingredient__batch_code', 'quantity'],
                'add_url': reverse('product-ingredient-add', kwargs={'pk': self.object.pk}),
            },
            {
                'title': 'Yield',
                'qs': self.object.yield_containers.select_related('container__container_type'),
                'fields': [
                    ('Name', 'container__container_type'),
                    'container__batch_code',
                    ('Quantity (units)', 'quantity'),
                    ('Total Volume (litres)', 'total_volume'),
                ],
                'add_url': reverse('yield-container-add', kwargs={'pk': self.object.pk}),
            },
        ]


product_details = ProductDetails.as_view()
