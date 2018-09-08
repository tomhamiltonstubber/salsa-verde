from devtools import debug
from django.shortcuts import redirect
from django.urls import reverse

from .base_views import DetailView, UpdateModelView, ListView, AddModelView
from SalsaVerde.main.forms import (ProductIngredientFormSet, UpdateProductForm, YieldContainersFormSet,
                                   UpdateProductTypeForm, ProductTypeSizesFormSet)
from SalsaVerde.main.models import Product, ProductType


class ProductTypeList(ListView):
    model = ProductType
    display_items = [
        'name',
        'ingredient_types',
    ]


product_type_list = ProductTypeList.as_view()


class ProductTypeDetails(DetailView):
    model = ProductType
    display_items = [
        'ingredient_types',
        'code',
    ]

    def extra_display_items(self):
        return [
            {
                'title': 'Sizes',
                'qs': self.object.product_type_sizes.all(),
                'fields': [
                    'size',
                    'sku_code',
                    'bar_code',
                ]
            }
        ]


product_type_details = ProductTypeDetails.as_view()


class ProductTypeAdd(AddModelView):
    model = ProductType
    form_class = UpdateProductTypeForm
    template_name = 'intake_goods_form.jinja'
    title = 'Add Product Type'
    formset_class = ProductTypeSizesFormSet

    def form_valid(self, form):
        obj = form.save()
        formset = self.formset_class(self.request.POST)
        if formset.is_valid():
            formset.instance = obj
            formset.save()
        else:
            print(formset.errors)
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        if self.request.POST:
            formset = self.formset_class(self.request.POST, instance=self.object)
        else:
            formset = self.formset_class(instance=self.object)
        return super().get_context_data(formsets=formset, **kwargs)


product_type_add = ProductTypeAdd.as_view()


class ProductTypeEdit(ProductTypeAdd, UpdateModelView):
    model = ProductType
    form_class = UpdateProductTypeForm


product_type_edit = ProductTypeEdit.as_view()


class ProductList(ListView):
    model = Product
    display_items = [
        'product_type',
        'date_of_infusion',
        'date_of_bottling',
        'date_of_best_before',
        'yield_quantity',
    ]

    def get_button_menu(self):
        return [
            {'name': 'Add Product', 'url': reverse('products-add')},
            {'name': 'Product Types', 'url': reverse('product-types')},
        ]


product_list = ProductList.as_view()


class ProductAdd(AddModelView):
    model = Product
    form_class = UpdateProductForm
    template_name = 'add_product_form.jinja'

    def form_valid(self, form):
        product_ingredient_formset = ProductIngredientFormSet(self.request.POST)
        yield_container_formset = YieldContainersFormSet(self.request.POST)
        obj = form.save()
        if product_ingredient_formset.is_valid():
            product_ingredient_formset.instance = obj
            product_ingredient_formset.save()
        else:
            return self.form_invalid(form)
        if yield_container_formset.is_valid():
            yield_container_formset.instance = obj
            yield_container_formset.save()
        else:
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        if self.request.POST:
            product_ingredient_forms = ProductIngredientFormSet(self.request.POST)
            yield_container_forms = YieldContainersFormSet(self.request.POST)
        else:
            product_ingredient_forms = ProductIngredientFormSet(instance=self.object)
            yield_container_forms = YieldContainersFormSet(instance=self.object)
            if self.object:
                product_ingredient_forms.extra = 0
                yield_container_forms.extra = 0
        return super().get_context_data(product_ingredient_forms=product_ingredient_forms,
                                        yield_container_forms=yield_container_forms,
                                        **kwargs)


product_add = ProductAdd.as_view()


class ProductEdit(ProductAdd, UpdateModelView):
    model = Product
    form_class = UpdateProductForm
    template_name = 'add_product_form.jinja'


product_edit = ProductEdit.as_view()


class ProductDetails(DetailView):
    model = Product
    display_items = [
        'product_type',
        'date_of_infusion',
        'date_of_bottling',
        'date_of_best_before',
        'yield_quantity',
    ]


product_details = ProductDetails.as_view()
