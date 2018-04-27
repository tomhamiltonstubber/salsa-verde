from django import forms

from SalsaVerde.main.models import (Ingredient, Supplier, IngredientType, User, Document, ProductType, ContainerType,
                                    Container, Product, ProductIngredient, YieldContainer)
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
        exclude = {'intake_user', 'intake_date', 'intake_document'}


IngredientsFormSet = forms.modelformset_factory(Ingredient,
                                                formset=EmptyQSFormSet,
                                                form=UpdateIngredientsForm,
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
            raise forms.ValidationError("You must enter size if this isn't a cap")
        return self.cleaned_data['type']


class UpdateContainerForm(SVModelForm):
    class Meta:
        model = Container
        exclude = {}


class UpdateProductTypeForm(SVModelForm):
    class Meta:
        model = ProductType
        exclude = {}


class ProductIngredientForm(SVModelForm):
    class Meta:
        model = ProductIngredient
        exclude = {'product'}


class YieldContainersForm(SVModelForm):
    container = forms.ModelChoiceField(Container.objects.exclude(container__type=ContainerType.TYPE_CAP))
    cap = forms.ModelChoiceField(Container.objects.filter(container__type=ContainerType.TYPE_CAP))

    def save(self, commit=True):
        super().save(commit)
        YieldContainer.objects.create(container=self.cleaned_data['cap'], quantity=self.cleaned_data['quantity'])

    class Meta:
        model = YieldContainer
        exclude = {'product'}


class UpdateProductForm(SVModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_type'].label = 'Product Type'

    class Meta:
        model = Product
        exclude = {'date_of_best_before', 'product_ingredients'}


ProductIngredientFormSet = forms.inlineformset_factory(Product, ProductIngredient, form=ProductIngredientForm, extra=1)
