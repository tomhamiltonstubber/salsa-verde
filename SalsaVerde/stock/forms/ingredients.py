import json

from django import forms

from SalsaVerde.stock.forms.base_forms import SVFilterForm, SVModelForm
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
    intake_notes = forms.CharField(widget=forms.Textarea({'rows': 2, 'class': 'resize-vertical-only'}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ingred_type_units_lu = dict(IngredientType.objects.request_qs(self.request).values_list('id', 'unit'))
        # Here we're adding data to the widget so that it renders on the page and we can access it in JS. The point
        # of this is to allow us to change the units of the quantity input based on the ingredient type.
        self.fields['quantity'].widget.attrs.update(
            {
                'step': 0.01,
                'input-group-label-lu': 'ingred_type_units',
                'input-group-text': 'Units',
                'ingred_type_units': json.dumps(ingred_type_units_lu),
                'linked-input-id': 'id_ingredient_type',
            },
        )

    class Meta:
        model = Ingredient
        fields = [
            'supplier',
            'ingredient_type',
            'quantity',
            'batch_code',
            'intake_notes',
            'intake_user',
            'intake_date',
        ]
        layout = [
            ['intake_date', 'intake_user'],
            ['ingredient_type', 'quantity'],
            ['supplier', 'batch_code'],
            ['intake_notes'],
        ]


class IngredientFilterForm(SVFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['finished'] = forms.ChoiceField(
            label='Finished',
            choices=[('not-finished', 'Not finished'), ('all', 'All'), ('finished', 'Finished')],
            required=False,
        )

    def filter_kwargs(self) -> dict:
        filter_kwargs = super().filter_kwargs()
        if fin_filter := filter_kwargs.pop('finished', None):
            if fin_filter == 'all':
                # We don't need to add a filter for all
                pass
            elif fin_filter == 'finished':
                filter_kwargs['finished'] = True
            else:
                filter_kwargs['finished'] = False
        return filter_kwargs

    class Meta:
        model = Ingredient
        fields = ['ingredient_type', 'supplier', 'intake_user', 'intake_date']
        layout = [
            ['ingredient_type', 'supplier'],
            ['intake_user', 'finished'],
            ['intake_date_from', 'intake_date_to'],
        ]
