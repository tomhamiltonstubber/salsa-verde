from django.urls import reverse

from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.models import Container


class ContainerList(ModelListView):
    model = Container
    display_items = ['container_type', 'batch_code', 'intake_date', 'supplier']
    order_by = 'container_type__name'
    icon = 'fa-jar'

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
