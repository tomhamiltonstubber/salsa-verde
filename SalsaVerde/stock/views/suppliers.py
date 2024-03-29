from django.urls import reverse

from SalsaVerde.stock.forms.suppliers import UpdateSupplierForm
from SalsaVerde.stock.models import Supplier

from ...common.views import AddModelView, DetailView, ModelListView, UpdateModelView


class SupplierList(ModelListView):
    model = Supplier
    display_items = [
        'name',
        'main_contact',
        'phone',
        'email',
    ]
    icon = 'fa-tractor'

    def get_button_menu(self):
        yield {'name': 'Add Supplier', 'url': reverse('suppliers-add'), 'icon': 'fa-plus'}


supplier_list = SupplierList.as_view()


class SupplierDetails(DetailView):
    model = Supplier
    display_items = [
        'name',
        ('Address', 'address'),
        'phone',
        'email',
    ]

    def extra_display_items(self):
        return [
            {
                'title': 'Supplied Raw Ingredients',
                'qs': self.object.ingredients.all(),
                'fields': [('Ingredient', 'name'), 'batch_code', 'quantity', 'intake_date'],
            },
            {
                'title': 'Supplied Containers',
                'qs': self.object.containers.all(),
                'fields': [('Container', 'name'), 'batch_code', 'quantity', 'intake_date'],
            },
            {
                'title': 'Associated Documents',
                'qs': self.object.documents.all(),
                'fields': [('Document', 'name'), 'date_created'],
                'add_url': reverse('documents-add') + f'?supplier={self.object.pk}',
            },
        ]


supplier_details = SupplierDetails.as_view()


class SupplierAdd(AddModelView):
    model = Supplier
    form_class = UpdateSupplierForm


supplier_add = SupplierAdd.as_view()


class SupplierEdit(UpdateModelView):
    model = Supplier
    form_class = UpdateSupplierForm


supplier_edit = SupplierEdit.as_view()
