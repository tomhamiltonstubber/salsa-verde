from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse

from SalsaVerde.stock.forms.base_forms import SVModelForm
from SalsaVerde.stock.models import Ingredient, Product, ProductIngredient, ProductType, ProductTypeSize


class UpdateProductTypeForm(SVModelForm):
    class Meta:
        model = ProductType
        fields = ['name', 'code', 'ingredient_types']
        layout = [
            ['name', 'code'],
            ['ingredient_types'],
        ]

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


ProductTypeSizesFormSet = forms.inlineformset_factory(
    ProductType, ProductTypeSize, UpdateProductTypeSizeForm, extra=1, can_delete=False
)


class ProductIngredientForm(SVModelForm):
    title = 'Ingredients'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ingredient'].queryset = (
            self.fields['ingredient'].queryset.filter(finished=False).select_related('ingredient_type')
        )

    class Meta:
        model = ProductIngredient
        exclude = {'product'}


class AddProductForm(SVModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_type'].label = 'Product Type'
        # In this form, we want to render the ingredient fields dynamically as the product type is chosen. So we add
        # 10 fields to the form, and then set the URL for the ingredient choices to be the product type chosen.
        self.fields['product_type'].widget.attrs['product-ingredient-choices-url-template'] = reverse(
            'product-ingredient-choices', kwargs={'pk': 999}
        )
        ingredient_qs = Ingredient.objects.request_qs(self.request).filter(finished=False)
        # I'm hoping there are a max of 10 ingredients here.
        for i in range(10):
            self.fields[f'ingredient_{i}'] = forms.ModelChoiceField(queryset=ingredient_qs, required=False)
            self.fields[f'ingredient_quantity_{i}'] = forms.DecimalField(required=False)

    def clean(self):
        has_ingredient = False
        for i in range(10):
            if self.cleaned_data.get(f'ingredient_{i}') and not self.cleaned_data.get(f'ingredient_quantity_{i}'):
                raise ValidationError({'__all__': 'Quantity is required'})
            elif self.cleaned_data.get(f'ingredient_quantity_{i}') and not self.cleaned_data.get(f'ingredient_{i}'):
                raise ValidationError({'__all__': 'Ingredient is required'})
            elif self.cleaned_data.get(f'ingredient_{i}') and self.cleaned_data.get(f'ingredient_quantity_{i}'):
                has_ingredient = True
        if not has_ingredient:
            raise ValidationError({'__all__': 'Ingredient and quantities are required'})
        return self.cleaned_data

    class Meta:
        model = Product
        fields = ['product_type', 'batch_code', 'date_of_infusion']


class UpdateProductForm(SVModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.status != Product.STATUS_BOTTLED:
            for f in ['batch_code_applied', 'best_before_applied', 'quality_check_successful']:
                self.fields.pop(f)

    class Meta:
        model = Product
        fields = [
            'date_of_bottling',
            'date_of_best_before',
            'yield_quantity',
            'batch_code',
            'batch_code_applied',
            'best_before_applied',
            'quality_check_successful',
        ]
