from django.urls import reverse

from SalsaVerde.common.views import ExtraContentView
from SalsaVerde.company.models import Company
from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.stock.models import ContainerType, IngredientType, ProductType


class Setup(ExtraContentView):
    title = 'Setup'
    model = Company

    def extra_display_items(self):
        return [
            {
                'title': 'Product Types',
                'qs': ProductType.objects.request_qs(self.request),
                'fields': ['name', 'ingredient_types', 'code'],
                'add_url': reverse('product-types-add'),
            },
            {
                'title': 'Ingredient Types',
                'qs': IngredientType.objects.request_qs(self.request),
                'fields': ['name', 'unit'],
                'add_url': reverse('ingredient-types-add'),
            },
            {
                'title': 'Container Types',
                'qs': ContainerType.objects.request_qs(self.request),
                'fields': ['name', 'size', 'type'],
                'add_url': reverse('container-types-add'),
            },
            {
                'title': 'Package Templates',
                'qs': PackageTemplate.objects.request_qs(self.request),
                'fields': ['name', 'length', 'width', 'height'],
                'add_url': reverse('package-temps-add'),
            },
        ]


setup = Setup.as_view()
