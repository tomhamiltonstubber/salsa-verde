from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from SalsaVerde.common.views import AddModelView, UpdateModelView
from SalsaVerde.stock.forms.containers import YieldContainersForm
from SalsaVerde.stock.forms.products import AddProductForm, ProductIngredientForm, UpdateProductForm
from SalsaVerde.stock.models import Ingredient, Product, ProductIngredient, ProductType, YieldContainer


def get_product_ingredient_choices(request, pk: int):
    product_type = get_object_or_404(
        ProductType.objects.request_qs(request).prefetch_related('ingredient_types'), pk=pk
    )
    ingreds = []
    for ingred_type in product_type.ingredient_types.all():
        choices = [
            (i.id, str(i))
            for i in (
                Ingredient.objects.request_qs(request)
                .filter(ingredient_type=ingred_type, finished=False)
                .select_related('ingredient_type')
            )
        ]
        ingreds.append({'choices': choices, 'unit': ingred_type.unit, 'name': ingred_type.name})
    return JsonResponse(ingreds, safe=False)


class ProductAdd(AddModelView):
    model = Product
    form_class = AddProductForm
    template_name = 'add_product_form.jinja'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.status = Product.STATUS_INFUSED
        obj.save()
        for i in range(10):
            if ingred := form.cleaned_data[f'ingredient_{i}']:
                quantity = form.cleaned_data[f'ingredient_quantity_{i}']
                ProductIngredient.objects.create(product=obj, ingredient=ingred, quantity=quantity)
            else:
                break
        messages.success(self.request, 'New product added')
        return redirect(obj.get_absolute_url())


product_add = ProductAdd.as_view()


class ProductEdit(UpdateModelView):
    model = Product
    form_class = UpdateProductForm


product_edit = ProductEdit.as_view()


@require_POST
def change_product_status(request, pk):
    obj = get_object_or_404(Product.objects.request_qs(request), pk=pk)
    obj.finished = not obj.finished
    obj.save(update_fields=['finished'])
    return redirect('product-details', pk=pk)


class ProductIngredientAdd(AddModelView):
    model = ProductIngredient
    title = 'Add another Ingredient'
    form_class = ProductIngredientForm

    def get_cancel_url(self) -> str:
        return self.product.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product.objects.request_qs(request), pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.product = self.product
        obj.save()
        return redirect(self.product.get_absolute_url())


product_ingredient_add = ProductIngredientAdd.as_view()


class YieldContainerAdd(AddModelView):
    model = YieldContainer
    form_class = YieldContainersForm

    def get_title(self):
        return f'Bottle for {self.product}'

    def get_cancel_url(self) -> str:
        return self.product.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product.objects.request_qs(request), pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.product = self.product
        obj.save()
        return redirect(self.product.get_absolute_url())


yield_container_add = YieldContainerAdd.as_view()
