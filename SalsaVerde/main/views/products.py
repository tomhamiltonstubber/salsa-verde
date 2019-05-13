import textwrap

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from SalsaVerde.main.forms.containers import YieldContainersFormSet, YieldContainersForm
from .base_views import DetailView, UpdateModelView, ListView, AddModelView, SVFormsetForm, DeleteObjectView
from SalsaVerde.main.forms.products import (ProductIngredientFormSet, UpdateProductForm, UpdateProductTypeForm,
                                            ProductTypeSizesFormSet, UpdateProductTypeSizeForm, AddProductTypeSizeForm,
                                            AddProductForm, BottleProductForm, ProductIngredientForm)
from SalsaVerde.main.models import Product, ProductType, ProductTypeSize, ProductIngredient, YieldContainer


class ProductTypeList(ListView):
    model = ProductType
    display_items = [
        'name',
        'ingredient_types',
    ]
    order_by = 'name'


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
                'add_url': reverse('product-type-sizes-add', kwargs={'product_type': self.object.pk}),
            }
        ]


product_type_details = ProductTypeDetails.as_view()


class ProductTypeSizeEdit(UpdateModelView):
    model = ProductTypeSize
    form_class = UpdateProductTypeSizeForm
    title = 'Edit Product Size Type'
    template_name = 'edit_product_type_size.jinja'

    def form_valid(self, form):
        super().form_valid(form)
        return redirect(reverse('product-types-details', kwargs={'pk': self.object.product_type.pk}))


product_size_type_edit = ProductTypeSizeEdit.as_view()


class ProductTypeSizeAdd(AddModelView):
    model = ProductTypeSize
    form_class = AddProductTypeSizeForm
    title = 'Add Product Size Type'

    def dispatch(self, request, *args, **kwargs):
        self.product_type = get_object_or_404(ProductType, pk=kwargs['product_type'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.product_type = self.product_type
        obj.save()
        return redirect(reverse('product-types-details', kwargs={'pk': self.product_type.pk}))


product_size_type_add = ProductTypeSizeAdd.as_view()


class ProductTypeSizeDelete(DeleteObjectView):
    model = ProductTypeSize

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model.objects.request_qs(request), pk=kwargs['pk'])
        pt_id = obj.product_type.id
        obj.delete()
        return redirect(reverse('product-types-details', kwargs={'pk': pt_id}))


product_size_type_delete = ProductTypeSizeDelete.as_view()


class ProductTypeAdd(SVFormsetForm, AddModelView):
    model = ProductType
    form_class = UpdateProductTypeForm
    template_name = 'formset_form.jinja'
    title = 'Add Product Type'
    formset_class = ProductTypeSizesFormSet

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
    order_by = '-date_of_bottling'
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related('product_type')

    def get_button_menu(self):
        return [
            {'name': 'Record new product infusion', 'url': reverse('products-add')},
        ]


product_list = ProductList.as_view()


class ProductAdd(SVFormsetForm, AddModelView):
    model = Product
    form_class = AddProductForm
    template_name = 'formset_form.jinja'
    formset_class = ProductIngredientFormSet

    def form_valid(self, form):
        formset = self.formset_class(self.request.POST)
        formset.full_clean()
        if formset.is_valid():
            obj = form.save()
            formset.instance = obj
            formset.save()
        else:
            return self.form_invalid(form)
        obj.status = Product.STATUS_INFUSED
        obj.save(update_fields=['status'])
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


class ProductDetails(DetailView):
    model = Product

    def get_title(self):
        return textwrap.shorten(self.object.product_type.name, width=35, placeholder='…') + self.object.batch_code

    def get_display_items(self):
        items = [
            'product_type',
            'date_of_infusion',
            'batch_code',
            ('Stage', 'get_status_display'),
        ]
        if self.object.status == Product.STATUS_BOTTLED:
            items += [
                'date_of_best_before',
                'yield_quantity',
                'best_before_applied',
                'quality_check_successful',
                'batch_code_applied',
            ]
        return items

    def get_button_menu(self):
        btns = list(super().get_button_menu())
        if self.object.status == Product.STATUS_INFUSED:
            btns = [btn for btn in btns if btn['name'] != 'Edit']
            btns.insert(1, {'name': 'Record bottling', 'rurl': 'products-bottle'})
        return btns

    def extra_display_items(self):
        return [
            {
                'title': 'Ingredients',
                'qs': self.object.product_ingredients.select_related('ingredient__ingredient_type'),
                'fields': [
                    ('Name', 'ingredient__ingredient_type'),
                    'ingredient__batch_code',
                    'quantity',
                ],
                'add_url': reverse('product-ingredient-add', kwargs={'pk': self.object.pk})
            },
            {
                'title': 'Yield',
                'qs': self.object.yield_containers.select_related('container__container_type'),
                'fields': [
                    ('Name', 'container__container_type'),
                    'container__batch_code',
                    ('Quantity (units)', 'quantity'),
                    ('Total Volume (litres)', 'total_volume'),
                ],
                'add_url': reverse('yield-container-add', kwargs={'pk': self.object.pk})
            },
        ]


product_details = ProductDetails.as_view()


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
