from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST

from SalsaVerde.common.views import SVFormsetForm, AddModelView, UpdateModelView
from SalsaVerde.stock.forms.containers import YieldContainersFormSet, YieldContainersForm
from SalsaVerde.stock.forms.products import AddProductForm, BottleProductForm, UpdateProductForm, ProductIngredientForm
from SalsaVerde.stock.models import Product, ProductIngredient, YieldContainer, ProductType, Ingredient


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
        obj.save(update_fields=['status'])
        ingred_quantities = form.cleaned_data['ingredient_quantities']
        for ingred_id, quantity in ingred_quantities.items():
            ProductIngredient.objects.create(product=obj, ingredient_id=ingred_id, quantity=quantity)

        messages.success(self.request, 'New product added')
        return redirect(obj.get_absolute_url())


product_add = ProductAdd.as_view()


class ProductBottle(SVFormsetForm, UpdateModelView):
    model = Product
    form_class = BottleProductForm
    template_name = 'formset_form.jinja'
    formset_class = YieldContainersFormSet

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().status != Product.STATUS_INFUSED:
            raise PermissionDenied('Product must be infused first')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        formset = self.formset_class(self.request.POST)
        formset.full_clean()
        if formset.is_valid():
            obj = form.save()
            obj.status = Product.STATUS_BOTTLED
            obj.save(update_fields=['status'])
            formset.instance = obj
            formset.save(commit=True)
        else:
            return self.form_invalid(form)
        return redirect(self.object.get_absolute_url())


product_bottle = ProductBottle.as_view()


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
    title = 'Add another Ingredient'
    form_class = YieldContainersForm

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product.objects.request_qs(request), pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.product = self.product
        obj.save()
        return redirect(self.product.get_absolute_url())


yield_container_add = YieldContainerAdd.as_view()
