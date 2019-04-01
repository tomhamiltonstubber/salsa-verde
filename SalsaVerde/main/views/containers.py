from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from SalsaVerde.main.forms.base_forms import GoodsIntakeForm
from SalsaVerde.main.forms.containers import UpdateContainerTypeForm, UpdateContainerForm, ContainersFormSet
from .base_views import UpdateModelView, ListView, AddModelView, DetailView, SVFormsetForm
from SalsaVerde.main.models import Container, ContainerType, Product


class ContainerTypeList(ListView):
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
                'qs': self.object.containers.select_related('container_type').order_by('-goods_intake__intake_date'),
                'fields': [
                    'container_type',
                    'batch_code',
                    ('Intake date', 'goods_intake__intake_date'),
                    'supplier',
                ],
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


class ContainerList(ListView):
    model = Container
    display_items = [
        'container_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'supplier',
    ]
    order_by = 'container_type__name'

    def dispatch(self, request, *args, **kwargs):
        self.view_finished = bool(self.request.GET.get('finished'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(finished=self.view_finished)
            .select_related('container_type', 'goods_intake', 'supplier')
        )

    def get_button_menu(self):
        yield {'name': 'Record containers intake', 'url': reverse('intake-containers')}
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
        ('Intake date', 'goods_intake__intake_date'),
        'obj_url|supplier',
        'quantity',
        ('Intake Document', 'obj_url|intake_document'),
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
            Product.objects
            .request_qs(self.request)
            .filter(yield_containers__container=self.object)
            .select_related('product_type')
            .order_by('-date_of_bottling')
        )
        return [
            {
                'title': 'Products used in',
                'qs': products,
                'fields': [
                    'product_type',
                    'batch_code',
                    'date_of_infusion',
                    'date_of_bottling',
                    'yield_quantity',
                ]
            },
        ]


containers_details = ContainerDetails.as_view()


class IntakeContainers(SVFormsetForm, AddModelView):
    model = Container
    formset_class = ContainersFormSet
    form_class = GoodsIntakeForm
    template_name = 'formset_form.jinja'
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
