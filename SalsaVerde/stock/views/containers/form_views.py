from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from SalsaVerde.common.views import AddModelView, UpdateModelView
from SalsaVerde.stock.forms.containers import ContainerForm

from SalsaVerde.stock.models import Container


@require_POST
def change_container_status(request, pk):
    obj = get_object_or_404(Container.objects.request_qs(request), pk=pk)
    obj.finished = not obj.finished
    obj.save(update_fields=['finished'])
    return redirect('containers-details', pk=pk)


class ContainersAdd(AddModelView):
    model = Container
    form_class = ContainerForm
    success_url = reverse_lazy('containers')
    title = 'Add Container'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'intake_user': self.request.user}
        return kwargs


container_add = ContainersAdd.as_view()


class ContainerEdit(UpdateModelView):
    model = Container
    form_class = ContainerForm
    title = 'Edit Container'


containers_edit = ContainerEdit.as_view()
