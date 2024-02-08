from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.models import ContainerType


class ContainerTypeList(ModelListView):
    model = ContainerType
    display_items = ['name', 'size', 'type']
    order_by = 'name'


container_type_list = ContainerTypeList.as_view()
