from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from SalsaVerde.stock.forms.ingredients import UpdateIngredientTypeForm, IngredientForm
from SalsaVerde.stock.models import Ingredient, IngredientType, Product

from ...common.views import AddModelView, DetailView, ModelListView, UpdateModelView


class IngredientTypeList(ModelListView):
    model = IngredientType
    display_items = ['name', 'unit']
    order_by = 'name'


ingredient_type_list = IngredientTypeList.as_view()


class IngredientTypeDetails(DetailView):
    model = IngredientType
    display_items = ['name', 'unit']

    def extra_display_items(self):
        return [
            {
                'title': 'Ingredients',
                'qs': self.object.ingredients.select_related('ingredient_type').order_by('-intake_date'),
                'fields': ['ingredient_type', 'batch_code', ('Intake date', 'intake_date'), 'supplier'],
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
        'quantity',
        'batch_code',
        'obj_url|supplier',
        'intake_date',
        'intake_user',
        'intake_quality_check',
        'finished',
        'intake_notes',
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
                'fields': ['product_type', 'batch_code', 'date_of_infusion', 'date_of_bottling', 'yield_quantity'],
                'icon': 'fa-bottle-droplet',
            }
        ]

    def get_button_menu(self):
        btns = super().get_button_menu()
        if self.object.finished:
            label = 'Mark as In stock'
        else:
            label = 'Mark as Finished'
        btns[-1].append(
            {
                'name': label,
                'url': reverse('ingredient-status', kwargs={'pk': self.object.pk}),
                'method': 'POST',
                'icon': 'fa-check',
            },
        )
        return btns


ingredient_details = IngredientDetails.as_view()


class IngredientEdit(UpdateModelView):
    model = Ingredient
    form_class = IngredientForm
    title = 'Edit Ingredient'
    cancel_rurl = 'ingredients'


ingredient_edit = IngredientEdit.as_view()


class IngredientAdd(AddModelView):
    success_url = reverse_lazy('ingredients')
    form_class = IngredientForm
    model = Ingredient
    title = 'Intake Ingredient'
    cancel_rurl = 'ingredients'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'intake_user': self.request.user}
        return kwargs


ingredient_add = IngredientAdd.as_view()
