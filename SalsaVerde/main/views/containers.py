from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from SalsaVerde.main.forms.base_forms import GoodsIntakeForm
from SalsaVerde.main.forms.containers import UpdateContainerTypeForm, UpdateContainerForm, ContainersFormSet
from .base_views import UpdateModelView, ListView, AddModelView, DetailView, SVFormsetForm, DeleteObjectView
from SalsaVerde.main.models import Container, ContainerType


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
        ('Supplier', 'func|get_supplier_link'),
        'quantity',
        ('Intake document', 'func|get_intake_document'),
        'finished',
    ]

    def get_supplier_link(self, obj):
        if obj.supplier:
            return mark_safe(f'<a href="{obj.supplier.get_absolute_url()}">{obj.supplier}</a>')
        return '–'

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


class IntakeContainers(SVFormsetForm, AddModelView):
    model = Container
    formset_classes = {'formset': ContainersFormSet}
    form_class = GoodsIntakeForm
    template_name = 'intake_goods_form.jinja'
    success_url = reverse_lazy('containers')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['document_type'] = self.model.intake_document_type()
        return kwargs


intake_containers = IntakeContainers.as_view()


class ContainerEdit(UpdateModelView):
    model = Container
    form_class = UpdateContainerForm


containers_edit = ContainerEdit.as_view()
