from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from SalsaVerde.main.forms.base_forms import GoodsIntakeForm
from SalsaVerde.main.forms.ingredients import IngredientsFormSet, UpdateIngredientsForm, UpdateIngredientTypeForm
from SalsaVerde.main.models import Ingredient, IngredientType, Product

from .base_views import AddModelView, DetailView, ListView, SVFormsetForm, UpdateModelView


class IngredientTypeList(ListView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]
    order_by = 'name'


ingredient_type_list = IngredientTypeList.as_view()


class IngredientTypeDetails(DetailView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]

    def extra_display_items(self):
        return [
            {
                'title': 'Ingredients',
                'qs': self.object.ingredients.select_related('ingredient_type').order_by('-goods_intake__intake_date'),
                'fields': ['ingredient_type', 'batch_code', ('Intake date', 'goods_intake__intake_date'), 'supplier',],
            }
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
    ]
    order_by = 'ingredient_type__name'

    def dispatch(self, request, *args, **kwargs):
        self.view_finished = bool(self.request.GET.get('finished'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(finished=self.view_finished)
            .select_related('ingredient_type', 'goods_intake', 'supplier')
        )

    def get_button_menu(self):
        yield {'name': 'Record ingredients intake', 'url': reverse('intake-ingredients')}
        if self.view_finished:
            yield {'name': 'View Current Ingredients', 'url': reverse('ingredients')}
        else:
            yield {'name': 'View Finished Ingredients', 'url': reverse('ingredients') + '?finished=true'}


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
        'obj_url|ingredient_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'obj_url|supplier',
        'quantity',
        ('Intake Document', 'obj_url|intake_document'),
        'intake_quality_check',
        'finished',
    ]

    def extra_display_items(self):
        products = (
            Product.objects.request_qs(self.request)
            .filter(product_ingredients__ingredient=self.object)
            .select_related('product_type')
            .order_by('-date_of_bottling')
        )
        return [
            {
                'title': 'Products used in',
                'qs': products,
                'fields': ['product_type', 'batch_code', 'date_of_infusion', 'date_of_bottling', 'yield_quantity',],
            }
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
