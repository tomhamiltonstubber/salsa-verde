from django.forms import ModelForm, modelformset_factory, BaseModelFormSet, forms, ModelChoiceField

from SalsaVerde.main.models import Ingredient, Supplier, IngredientType, User, Document, ProductType


class SVModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


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


class EmptyQSFormSet(BaseModelFormSet):
    def get_queryset(self):
        return Ingredient.objects.none()


class IngredientsForm(SVModelForm):
    class Meta:
        model = Ingredient
        exclude = {'intake_user', 'intake_date', 'intake_document'}


IngredientsFormSet = modelformset_factory(Ingredient, formset=EmptyQSFormSet, form=IngredientsForm, can_delete=False)


class UpdateDocumentForm(SVModelForm):
    focus = ModelChoiceField(User.objects.all(), label='Associated with', required=False,
                             help_text='This is for associated documents with a user, such as a return to work form')
    author = ModelChoiceField(User.objects.all(), label='Author', required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['author'].initial = self.request.user
            self.fields['file'].required = False

    class Meta:
        model = Document
        exclude = {'edits', 'date_created'}


class UpdateProductTypeForm(SVModelForm):
    class Meta:
        model = ProductType
        exclude = {}
