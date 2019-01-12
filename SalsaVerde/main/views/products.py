from django.shortcuts import redirect
from django.urls import reverse

from .base_views import DetailView, UpdateModelView, ListView, AddModelView, SVFormsetForm
from SalsaVerde.main.forms import (ProductIngredientFormSet, UpdateProductForm, YieldContainersFormSet,
                                   UpdateProductTypeForm, ProductTypeSizesFormSet, ProductTypeSizeForm)
from SalsaVerde.main.models import Product, ProductType, ProductTypeSize


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
                ],
            }
        ]


product_type_details = ProductTypeDetails.as_view()


class ProductTypeSizeEdit(UpdateModelView):
    model = ProductTypeSize
    form_class = ProductTypeSizeForm
    title = 'Edit Product Size Type'

    def form_valid(self, form):
        super().form_valid(form)
        return redirect(reverse('product-types-details', kwargs={'pk': self.object.product_type.pk}))


product_size_type_edit = ProductTypeSizeEdit.as_view()


class ProductTypeAdd(SVFormsetForm, AddModelView):
    model = ProductType
    form_class = UpdateProductTypeForm
    template_name = 'intake_goods_form.jinja'
    title = 'Add Product Type'
    formset_classes = {'formset': ProductTypeSizesFormSet}

    def get_success_url(self):
        return self.object.get_absolute_url()


product_type_add = ProductTypeAdd.as_view()


class ProductTypeEdit(UpdateModelView):
    model = ProductType
    form_class = UpdateProductTypeForm

    def get_title(self):
        return f'Edit {self.object}'


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


class ProductAdd(SVFormsetForm, AddModelView):
    model = Product
    form_class = UpdateProductForm
    template_name = 'add_product_form.jinja'
    formset_classes = {
        'product_ingredient_formset': ProductIngredientFormSet,
        'yield_container_formset': YieldContainersFormSet
    }

    def get_success_url(self):
        return self.object.get_absolute_url()


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
