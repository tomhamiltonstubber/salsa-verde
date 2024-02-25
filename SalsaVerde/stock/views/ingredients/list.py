from django.urls import reverse

from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.models import Ingredient


class IngredientList(ModelListView):
    model = Ingredient
    display_items = ['ingredient_type', 'batch_code', 'intake_date', 'supplier']
    order_by = 'ingredient_type__name'
    icon = 'fa-apple-whole'

    def dispatch(self, request, *args, **kwargs):
        self.view_finished = bool(self.request.GET.get('finished'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(finished=self.view_finished).select_related('ingredient_type', 'supplier')

    def get_button_menu(self):
        yield {'name': 'Record ingredients intake', 'url': reverse('ingredient-add'), 'icon': 'fa-plus'}
        if self.view_finished:
            yield {'name': 'View Current Ingredients', 'url': reverse('ingredients')}
        else:
            yield {'name': 'View Finished Ingredients', 'url': reverse('ingredients') + '?finished=true'}


ingredient_list = IngredientList.as_view()
