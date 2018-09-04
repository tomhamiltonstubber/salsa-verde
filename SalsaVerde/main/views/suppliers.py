from django.urls import reverse

from .base_views import UpdateModelView, AddModelView, DetailView, ListView
from SalsaVerde.main.forms import UpdateSupplierForm
from SalsaVerde.main.models import Supplier


class SupplierList(ListView):
    model = Supplier
    display_items = [
        'name',
        'main_contact',
        'phone',
        'email',
    ]


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
                'title': 'Supplied Ingredients',
                'qs': self.object.ingredients.all(),
                'fields': [
                    ('Ingredient', 'name'),
                    'batch_code',
                    'quantity',
                    ('Intake date', 'goods_intake__intake_date'),
                    ('Intake document', 'intake_document'),
                ]
            },
            {
                'title': 'Supplied Containers',
                'qs': self.object.containers.all(),
                'fields': [
                    ('Container', 'name'),
                    'batch_code',
                    'quantity',
                    ('Intake date', 'goods_intake__intake_date'),
                    ('Intake document', 'intake_document'),
                ]
            },
            {
                'title': 'Associated Documents',
                'qs': self.object.documents.all(),
                'fields': [
                    ('Document', 'name'),
                    'date_created',
                ],
                'add_url': reverse('documents-add') + f'?supplier={self.object.pk}'
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
