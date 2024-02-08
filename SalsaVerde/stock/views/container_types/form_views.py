from SalsaVerde.common.views import AddModelView, UpdateModelView
from SalsaVerde.stock.forms.containers import UpdateContainerTypeForm
from SalsaVerde.stock.models import ContainerType


class ContainerTypeAdd(AddModelView):
    model = ContainerType
    form_class = UpdateContainerTypeForm


container_type_add = ContainerTypeAdd.as_view()


class ContainerTypeEdit(UpdateModelView):
    model = ContainerType
    form_class = UpdateContainerTypeForm


container_type_edit = ContainerTypeEdit.as_view()
