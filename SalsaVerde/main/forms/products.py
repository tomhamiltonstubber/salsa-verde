from django import forms

from SalsaVerde.main.forms.base_forms import SVModelForm
from SalsaVerde.main.models import ProductType, ProductTypeSize, ProductIngredient, Product


class UpdateProductTypeForm(SVModelForm):
    class Meta:
        model = ProductType
        exclude = {'company'}

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.request.user.company
        return super().save(commit)


class AddProductTypeSizeForm(SVModelForm):
    title = 'Product Type Sizes'

    class Meta:
        model = ProductTypeSize
        fields = ['name', 'size', 'sku_code', 'bar_code']


class UpdateProductTypeSizeForm(SVModelForm):
    title = 'Product Type Sizes'

    class Meta:
        model = ProductTypeSize
        fields = ['name', 'size', 'sku_code', 'bar_code']


ProductTypeSizesFormSet = forms.inlineformset_factory(ProductType, ProductTypeSize, UpdateProductTypeSizeForm, extra=1,
                                                      can_delete=False)


class ProductIngredientForm(SVModelForm):
    title = 'Ingredients'

    class Meta:
        model = ProductIngredient
        exclude = {'product'}


ProductIngredientFormSet = forms.inlineformset_factory(Product, ProductIngredient, form=ProductIngredientForm, extra=1,
                                                       can_delete=False)


class AddProductForm(SVModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_type'].label = 'Product Type'

    class Meta:
        model = Product
        fields = ['product_type', 'batch_code', 'date_of_infusion']


class BottleProductForm(SVModelForm):
    class Meta:
        model = Product
        fields = ['date_of_bottling', 'date_of_best_before', 'yield_quantity']


class UpdateProductForm(SVModelForm):
    class Meta:
        model = Product
        fields = ['date_of_bottling', 'date_of_best_before', 'yield_quantity', 'batch_code']
