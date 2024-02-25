from django.urls import reverse

from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.forms.ingredients import IngredientFilterForm
from SalsaVerde.stock.models import Ingredient


class IngredientList(ModelListView):
    model = Ingredient
    display_items = ['ingredient_type', 'batch_code', 'intake_date', 'supplier', 'quantity']
    order_by = 'ingredient_type__name'
    icon = 'fa-apple-whole'
    filter_form = IngredientFilterForm

    def get_queryset(self):
        qs = super().get_queryset().select_related('ingredient_type', 'supplier')
        if 'finished' not in self._mutable_get_args:
            qs = qs.filter(finished=False)
        return qs

    def get_button_menu(self):
        yield {'name': 'Record ingredients intake', 'url': reverse('ingredient-add'), 'icon': 'fa-plus'}


ingredient_list = IngredientList.as_view()
