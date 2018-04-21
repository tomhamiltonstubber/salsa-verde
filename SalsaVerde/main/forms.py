from django.forms import ModelForm, modelformset_factory, BaseModelFormSet

from SalsaVerde.main.models import Ingredient, Supplier, IngredientType, User


class UpdateUserForm(ModelForm):
    class Meta:
        model = User
        fields = {'email', 'first_name', 'last_name', 'street', 'town', 'country', 'postcode', 'phone'}


class UpdateSupplierForm(ModelForm):
    class Meta:
        model = Supplier
        exclude = {}


class UpdateIngredientTypeForm(ModelForm):
    class Meta:
        model = IngredientType
        exclude = {}


class EmptyQSFormSet(BaseModelFormSet):
    def get_queryset(self):
        return Ingredient.objects.none()


class IngredientsForm(ModelForm):
    class Meta:
        model = Ingredient
        exclude = {'intake_user', 'intake_date', 'intake_document'}


IngredientsFormSet = modelformset_factory(Ingredient, formset=EmptyQSFormSet, form=IngredientsForm, can_delete=False)
