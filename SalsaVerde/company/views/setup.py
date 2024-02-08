from django.urls import reverse, reverse_lazy

from SalsaVerde.common.views import ExtraContentView, UpdateModelView
from SalsaVerde.company.forms import EditCompanyForm
from SalsaVerde.company.models import Company
from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.stock.models import ContainerType, IngredientType, ProductType


class EditCompany(UpdateModelView):
    model = Company
    title = 'Edit company'
    form_class = EditCompanyForm
    success_url = cancel_url = reverse_lazy('setup')

    def get_object(self, *args, **kwargs):
        return self.request.user.company


edit_company = EditCompany.as_view()


class Setup(ExtraContentView):
    title = 'Setup'
    model = Company
    display_items = [
        'name',
        ('Address', 'address_str'),
        'website',
        ('Main contact', 'get_main_contact'),
        'shopify_domain',
    ]

    def get_button_menu(self):
        yield {'rurl': 'setup-company', 'name': 'Edit company settings'}

    def dispatch(self, request, *args, **kwargs):
        self.object = self.request.user.company
        return super().dispatch(request, *args, **kwargs)

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

    def get_context_data(self, **kwargs):
        display_vals = self.get_display_values(self.object, self.get_display_items())
        display_labels = self.get_display_labels(self.get_display_items())
        return super().get_context_data(display_items=zip(display_labels, display_vals), **kwargs)


setup = Setup.as_view()
