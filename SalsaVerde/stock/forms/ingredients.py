from django import forms

from SalsaVerde.stock.forms.base_forms import SVModelForm
from SalsaVerde.stock.models import Ingredient, IngredientType


class UpdateIngredientTypeForm(SVModelForm):
    class Meta:
        model = IngredientType
        exclude = {'company'}

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.request.user.company
        return super().save(commit)


class IngredientForm(SVModelForm):
    title = 'Ingredients'
    intake_date = forms.DateTimeField()
    intake_notes = forms.CharField(widget=forms.Textarea({'rows': 2, 'class': 'resize-vertical-only'}), required=False)

    class Meta:
        model = Ingredient
        fields = ['supplier', 'ingredient_type', 'quantity', 'batch_code', 'intake_quality_check', 'intake_notes']
        layout = [
            ['ingredient_type', 'quantity'],
            ['supplier', 'batch_code'],
            [('intake_notes', 9), 'intake_quality_check'],
        ]
