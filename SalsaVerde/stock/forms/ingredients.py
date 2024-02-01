from django import forms

from SalsaVerde.stock.forms.base_forms import SVModelForm
from SalsaVerde.stock.models import GoodsIntake, Ingredient, IngredientType


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
        fields = ['supplier', 'ingredient_type', 'quantity', 'batch_code', 'intake_quality_check', 'intake_notes']
        layout = [
            ['ingredient_type', 'quantity', 'batch_code', 'supplier'],
            ['intake_notes', 'intake_quality_check'],
        ]


IngredientsFormSet = forms.inlineformset_factory(
    GoodsIntake, Ingredient, form=UpdateIngredientsForm, extra=1, can_delete=False
)
