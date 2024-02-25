from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.models import IngredientType


class IngredientTypeList(ModelListView):
    model = IngredientType
    display_items = ['name', 'unit']
    order_by = 'name'


ingredient_type_list = IngredientTypeList.as_view()
