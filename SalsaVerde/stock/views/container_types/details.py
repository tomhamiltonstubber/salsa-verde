from SalsaVerde.common.views import DetailView
from SalsaVerde.stock.models import ContainerType


class ContainerTypeDetails(DetailView):
    model = ContainerType
    display_items = ['name', 'size', 'type']

    def extra_display_items(self):
        return [
            {
                'title': 'Containers',
                'qs': self.object.containers.select_related('container_type').order_by('-intake_date'),
                'fields': ['container_type', 'batch_code', ('Intake date', 'intake_date'), 'supplier'],
            }
        ]


container_type_details = ContainerTypeDetails.as_view()
