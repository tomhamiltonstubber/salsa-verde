from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from SalsaVerde.stock.forms.containers import ContainerForm, UpdateContainerTypeForm
from SalsaVerde.stock.models import Container, ContainerType, Product

from ...common.views import AddModelView, DetailView, ModelListView, SVFormsetForm, UpdateModelView


class ContainerTypeList(ModelListView):
    model = ContainerType
    display_items = [
        'name',
        'size',
        'type',
    ]
    order_by = 'name'


container_type_list = ContainerTypeList.as_view()


class ContainerTypeDetails(DetailView):
    model = ContainerType
    display_items = [
        'name',
        'size',
        'type',
    ]

    def extra_display_items(self):
        return [
            {
                'title': 'Containers',
                'qs': self.object.containers.select_related('container_type').order_by('-intake_date'),
                'fields': ['container_type', 'batch_code', ('Intake date', 'intake_date'), 'supplier'],
            }
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


class ContainerList(ModelListView):
    model = Container
    display_items = ['container_type', 'batch_code', 'intake_date', 'supplier']
    order_by = 'container_type__name'

    def dispatch(self, request, *args, **kwargs):
        self.view_finished = bool(self.request.GET.get('finished'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(finished=self.view_finished).select_related('container_type', 'supplier')

    def get_button_menu(self):
        yield {'name': 'Record containers intake', 'url': reverse('container-add'), 'icon': 'fa-plus'}
        if self.view_finished:
            yield {'name': 'View Current Containers', 'url': reverse('containers')}
        else:
            yield {'name': 'View Finished Containers', 'url': reverse('containers') + '?finished=true'}


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
        'intake_date',
        'obj_url|supplier',
        'quantity',
        'intake_quality_check',
        'finished',
    ]

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
        products = (
            Product.objects.request_qs(self.request)
            .filter(yield_containers__container=self.object)
            .select_related('product_type')
            .order_by('-date_of_bottling')
        )
        return [
            {
                'title': 'Products used in',
                'qs': products,
                'fields': ['product_type', 'batch_code', 'date_of_infusion', 'date_of_bottling', 'yield_quantity'],
            },
        ]


containers_details = ContainerDetails.as_view()


class ContainersAdd(AddModelView):
    model = Container
    form_class = ContainerForm
    success_url = reverse_lazy('containers')
    title = 'Add Containers'


container_add = ContainersAdd.as_view()


class ContainerEdit(UpdateModelView):
    model = Container
    form_class = ContainerForm
    title = 'Edit Containers'


containers_edit = ContainerEdit.as_view()
