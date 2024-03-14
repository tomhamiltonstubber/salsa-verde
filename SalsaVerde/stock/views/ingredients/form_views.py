from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from SalsaVerde.common.views import AddModelView, UpdateModelView
from SalsaVerde.stock.forms.ingredients import IngredientForm
from SalsaVerde.stock.models import Ingredient


@require_POST
def change_ingredient_status(request, pk):
    obj = get_object_or_404(Ingredient.objects.request_qs(request), pk=pk)
    obj.finished = not obj.finished
    obj.save(update_fields=['finished'])
    return redirect('ingredients-details', pk=pk)


class IngredientAdd(AddModelView):
    form_class = IngredientForm
    model = Ingredient
    cancel_url = reverse_lazy('ingredients')
    title = 'Add Raw Ingredient'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'intake_user': self.request.user}
        return kwargs


ingredient_add = IngredientAdd.as_view()


class IngredientEdit(UpdateModelView):
    model = Ingredient
    form_class = IngredientForm
    title = 'Edit Raw Ingredient'


ingredient_edit = IngredientEdit.as_view()
