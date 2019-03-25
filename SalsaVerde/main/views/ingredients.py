from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe

from django.views.decorators.http import require_POST

from .base_views import DetailView, UpdateModelView, ListView, AddModelView, SVFormsetForm
from SalsaVerde.main.forms.base_forms import GoodsIntakeForm
from SalsaVerde.main.forms.ingredients import UpdateIngredientTypeForm, UpdateIngredientsForm, IngredientsFormSet
from SalsaVerde.main.models import Ingredient, IngredientType


class IngredientTypeList(ListView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]


ingredient_type_list = IngredientTypeList.as_view()


class IngredientTypeDetails(DetailView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]


ingredient_type_details = IngredientTypeDetails.as_view()


class IngredientTypeAdd(AddModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_add = IngredientTypeAdd.as_view()


class IngredientTypeEdit(UpdateModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_edit = IngredientTypeEdit.as_view()


class IngredientList(ListView):
    model = Ingredient
    display_items = [
        'ingredient_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'supplier',
        'finished',
    ]

    def get_button_menu(self):
        return [
            {'name': 'Record ingredients intake', 'url': reverse('intake-ingredients')},
        ]


ingredient_list = IngredientList.as_view()


@require_POST
def change_ingredient_status(request, pk):
    obj = get_object_or_404(Ingredient.objects.request_qs(request), pk=pk)
    obj.finished = not obj.finished
    obj.save(update_fields=['finished'])
    return redirect('ingredients-details', pk=pk)


class IngredientDetails(DetailView):
    model = Ingredient
    display_items = [
        'ingredient_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'supplier',
        'quantity',
        ('Intake document', 'func|get_intake_document'),
        'finished',
    ]

    def get_button_menu(self):
        btns = super().get_button_menu()
        if self.object.finished:
            label = 'Mark as In stock'
        else:
            label = 'Mark as Finished'
        btns.append(
            {'name': label, 'url': reverse('ingredient-status', kwargs={'pk': self.object.pk}), 'method': 'POST'}
        )
        return btns

    def get_intake_document(self, obj):
        if obj.intake_document:
            return mark_safe(f'<a href="{obj.intake_document.get_absolute_url()}">{obj.intake_document}</a>')
        return '–'


ingredient_details = IngredientDetails.as_view()


class IngredientEdit(UpdateModelView):
    model = Ingredient
    form_class = UpdateIngredientsForm


ingredient_edit = IngredientEdit.as_view()


class IntakeIngredients(SVFormsetForm, AddModelView):
    success_url = reverse_lazy('ingredients')
    formset_class = IngredientsFormSet
    form_class = GoodsIntakeForm
    template_name = 'formset_form.jinja'
    model = Ingredient
    title = 'Intake Ingredients'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['document_type'] = self.model.intake_document_type()
        return kwargs


intake_ingredients = IntakeIngredients.as_view()
