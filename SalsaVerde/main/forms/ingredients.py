from django import forms

from SalsaVerde.main.forms.base_forms import SVModelForm
from SalsaVerde.main.models import IngredientType, Ingredient, GoodsIntake


class UpdateIngredientTypeForm(SVModelForm):
    class Meta:
        model = IngredientType
        exclude = {'company'}

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.request.user.company
        return super().save(commit)


class UpdateIngredientsForm(SVModelForm):
    title = 'Ingredients'

    class Meta:
        model = Ingredient
        fields = ['ingredient_type', 'quantity', 'batch_code', 'supplier']


IngredientsFormSet = forms.inlineformset_factory(GoodsIntake,
                                                 Ingredient,
                                                 form=UpdateIngredientsForm,
                                                 extra=1,
                                                 can_delete=False)
