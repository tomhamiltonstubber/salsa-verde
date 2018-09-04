from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from .base_views import UpdateModelView, ListView, AddModelView, DetailView
from .common import AddGoodsIntake
from SalsaVerde.main.forms import UpdateContainerForm, ContainersFormSet, UpdateContainerTypeForm
from SalsaVerde.main.models import Container, Document, ContainerType


class ContainerTypeList(ListView):
    model = ContainerType
    display_items = [
        'name',
        'size',
        'type',
    ]


container_type_list = ContainerTypeList.as_view()


class ContainerTypeDetails(DetailView):
    model = ContainerType
    display_items = [
        'name',
        'size',
        'type',
    ]


container_type_details = ContainerTypeDetails.as_view()


class ContainerTypeAdd(AddModelView):
    model = ContainerType
    form_class = UpdateContainerTypeForm


container_type_add = ContainerTypeAdd.as_view()


class ContainerTypeEdit(UpdateModelView):
    model = ContainerType
    form_class = UpdateContainerTypeForm


container_type_edit = ContainerTypeEdit.as_view()


class ContainerList(ListView):
    model = Container
    display_items = [
        'container_type',
        'batch_code',
        'finished',
    ]

    def get_button_menu(self):
        return [
            {'name': 'Record containers intake', 'url': reverse('intake-containers')},
            {'name': 'Container Types', 'url': reverse('container-types')},
        ]


containers_list = ContainerList.as_view()


@require_POST
def change_container_status(request, pk):
    obj = get_object_or_404(Container.objects.request_qs(request), pk=pk)
    obj.finished = not obj.finished
    obj.save(update_fields=['finished'])
    return redirect('containers-details', pk=pk)


class ContainerDetails(DetailView):
    model = Container
    display_items = [
        'container_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'supplier',
        'quantity',
        ('Intake document', 'func|get_intake_document'),
        'finished',
    ]

    def get_intake_document(self, obj):
        if obj.intake_document:
            return mark_safe(f'<a href="{obj.intake_document.get_absolute_url()}">{obj.intake_document}</a>')
        return '–'

    def get_button_menu(self):
        btns = super().get_button_menu()
        if self.object.finished:
            label = 'Mark as In stock'
        else:
            label = 'Mark as Finished'
        btns.append(
            {'name': label, 'url': reverse('container-status', kwargs={'pk': self.object.pk}), 'method': 'POST'}
        )
        return btns

    def extra_display_items(self):
        return [
            {
                'title': 'Products used in',
                'qs': self.object.yield_containers.select_related('product'),
                'fields': [
                    ('Product', 'product__product_type__name'),
                    ('Batch code', 'product__batch_code'),
                    ('Date of infusion', 'product__date_of_infusion'),
                    ('Date of bottling', 'product__date_of_bottling'),
                    ('Best before', 'product__date_of_best_before'),
                    ('Quantity', 'product__yield_quantity'),
                ]
            },
        ]


containers_details = ContainerDetails.as_view()


class IntakeContainers(AddGoodsIntake, AddModelView):
    model = Container
    document_type = Document.FORM_SUP02
    goods_model_formset = ContainersFormSet
    success_url = 'containers'


intake_containers = IntakeContainers.as_view()


class ContainerEdit(UpdateModelView):
    model = Container
    form_class = UpdateContainerForm


containers_edit = ContainerEdit.as_view()
