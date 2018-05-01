from django import forms

from SalsaVerde.main.models import (Ingredient, Supplier, IngredientType, User, Document, ProductType, ContainerType,
                                    Container, Product, ProductIngredient, YieldContainer, GoodsIntake)
from SalsaVerde.main.widgets import DateTimePicker


class SVModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.DateTimeInput):
                self.fields[field].widget = DateTimePicker(self.fields[field])


class UpdateUserForm(SVModelForm):
    class Meta:
        model = User
        fields = {'email', 'first_name', 'last_name', 'street', 'town', 'country', 'postcode', 'phone'}


class UpdateSupplierForm(SVModelForm):
    class Meta:
        model = Supplier
        exclude = {}


class UpdateIngredientTypeForm(SVModelForm):
    class Meta:
        model = IngredientType
        exclude = {}


class EmptyQSFormSet(forms.BaseModelFormSet):
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return Ingredient.objects.none()


class UpdateIngredientsForm(SVModelForm):
    class Meta:
        model = Ingredient
        fields = ['ingredient_type', 'quantity', 'batch_code', 'supplier', 'condition', 'status']


IngredientsFormSet = forms.inlineformset_factory(GoodsIntake,
                                                 Ingredient,
                                                 form=UpdateIngredientsForm,
                                                 extra=1,
                                                 can_delete=False)


class UpdateDocumentForm(SVModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['author'].initial = self.request.user
            self.fields['file'].required = False

    class Meta:
        model = Document
        exclude = {'edits', 'date_created'}


class UpdateContainerTypeForm(SVModelForm):
    class Meta:
        model = ContainerType
        exclude = {}

    def clean_type(self):
        if self.cleaned_data['type'] != ContainerType.TYPE_CAP and not self.cleaned_data['size']:
            raise forms.ValidationError("You must enter a size if this isn't a cap")
        return self.cleaned_data['type']


class UpdateContainerForm(SVModelForm):
    class Meta:
        model = Container
        fields = ['container_type', 'quantity', 'batch_code', 'supplier', 'condition', 'status']


ContainersFormSet = forms.inlineformset_factory(GoodsIntake,
                                                Container,
                                                UpdateContainerForm,
                                                extra=1,
                                                can_delete=False)


class UpdateProductTypeForm(SVModelForm):
    class Meta:
        model = ProductType
        exclude = {}


class ProductIngredientForm(SVModelForm):
    class Meta:
        model = ProductIngredient
        exclude = {'product'}


class YieldContainersForm(SVModelForm):
    container = forms.ModelChoiceField(Container.objects.exclude(container_type__type=ContainerType.TYPE_CAP))
    cap = forms.ModelChoiceField(Container.objects.filter(container_type__type=ContainerType.TYPE_CAP))

    def save(self, commit=True):
        obj = super().save(commit)
        YieldContainer.objects.create(
            container=self.cleaned_data['cap'],
            quantity=self.cleaned_data['quantity'],
            product_id=obj.product.id
        )
        return obj

    class Meta:
        model = YieldContainer
        exclude = {'product'}


YieldContainersFormSet = forms.inlineformset_factory(Product, YieldContainer, YieldContainersForm, extra=1)


class UpdateProductForm(SVModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_type'].label = 'Product Type'

    class Meta:
        model = Product
        exclude = {'date_of_best_before', 'product_ingredients'}


ProductIngredientFormSet = forms.inlineformset_factory(Product, ProductIngredient, form=ProductIngredientForm, extra=1)


class GoodsIntakeForm(SVModelForm):
    class Meta:
        model = GoodsIntake
        exclude = {'date_created'}
