from django.urls import reverse

from SalsaVerde.common.views import DetailView
from SalsaVerde.stock.models import Ingredient, Product


class IngredientDetails(DetailView):
    model = Ingredient
    display_items = [
        'obj_url|ingredient_type',
        'quantity',
        'batch_code',
        'obj_url|supplier',
        'intake_date',
        'intake_user',
        'intake_quality_check',
        'finished',
        'intake_notes',
    ]

    def extra_display_items(self):
        products = (
            Product.objects.request_qs(self.request)
            .filter(product_ingredients__ingredient=self.object)
            .select_related('product_type')
            .order_by('-date_of_bottling')
        )
        return [
            {
                'title': 'Products used in',
                'qs': products,
                'fields': ['product_type', 'batch_code', 'date_of_infusion', 'date_of_bottling', 'yield_quantity'],
                'icon': 'fa-bottle-droplet',
            }
        ]

    def get_button_menu(self):
        btns = super().get_button_menu()
        if self.object.finished:
            label = 'Mark as In stock'
        else:
            label = 'Mark as Finished'
        btns.append(
            {
                'name': label,
                'url': reverse('ingredient-status', kwargs={'pk': self.object.pk}),
                'method': 'POST',
                'icon': 'fa-check',
                'group': 2,
            },
        )
        return btns


ingredient_details = IngredientDetails.as_view()
