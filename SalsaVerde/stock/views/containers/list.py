from django import forms
from django.urls import reverse

from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.forms.base_forms import SVFilterForm
from SalsaVerde.stock.models import Container


class ContainerFilterForm(SVFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['finished'] = forms.ChoiceField(
            label='Finished',
            choices=[('not-finished', 'Not finished'), ('all', 'All'), ('finished', 'Finished')],
            required=False,
        )

    def filter_kwargs(self) -> dict:
        filter_kwargs = super().filter_kwargs()
        if fin_filter := filter_kwargs.pop('finished', None):
            if fin_filter == 'all':
                # We don't need to add a filter for all
                pass
            elif fin_filter == 'finished':
                filter_kwargs['finished'] = True
            else:
                filter_kwargs['finished'] = False
        return filter_kwargs

    class Meta:
        model = Container
        fields = ['container_type', 'supplier', 'intake_user', 'intake_date']
        layout = [
            ['container_type', 'supplier'],
            ['intake_user', 'finished'],
            ['intake_date_from', 'intake_date_to'],
        ]


class ContainerList(ModelListView):
    model = Container
    display_items = ['container_type', 'batch_code', 'intake_date', 'supplier']
    order_by = 'container_type__name'
    icon = 'fa-jar'
    filter_form = ContainerFilterForm

    def get_queryset(self):
        qs = super().get_queryset().select_related('container_type', 'supplier')
        if 'finished' not in self._mutable_get_args:
            qs = qs.filter(finished=False)
        return qs

    def get_button_menu(self):
        yield {'name': 'Record packaging intake', 'url': reverse('container-add'), 'icon': 'fa-plus'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self._propped_filter_form and self._propped_filter_form.filter_kwargs() == {'finished': False}:
            context['start_filter_form_open'] = False
        return context


containers_list = ContainerList.as_view()
