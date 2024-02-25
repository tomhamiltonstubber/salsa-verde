from SalsaVerde.common.views import AddModelView, UpdateModelView
from SalsaVerde.stock.forms.ingredients import UpdateIngredientTypeForm
from SalsaVerde.stock.models import IngredientType


class IngredientTypeAdd(AddModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_add = IngredientTypeAdd.as_view()


class IngredientTypeEdit(UpdateModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_edit = IngredientTypeEdit.as_view()
