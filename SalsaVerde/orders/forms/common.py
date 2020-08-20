from django import forms
from django.forms import BaseFormSet

from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.stock.forms.base_forms import SVForm
from SalsaVerde.stock.models import Product


class PackageForm(SVForm):
    title = 'Packages sending'

    package_type = forms.ModelChoiceField(PackageTemplate.objects.none(), required=False)
    length = forms.DecimalField(label='Length (cm)', decimal_places=1, min_value=0)
    width = forms.DecimalField(label='Width (cm)', decimal_places=1, min_value=0)
    height = forms.DecimalField(label='Height (cm)', decimal_places=1, min_value=0)
    weight = forms.DecimalField(label='Weight (kg)', decimal_places=2, min_value=0)


PackageFormSet = forms.formset_factory(PackageForm)


class SVBaseFormSet(BaseFormSet):
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        return super()._construct_form(i, request=self.request, **kwargs)

    @property
    def empty_form(self):
        form = self.form(
            request=self.request,
            prefix=self.add_prefix('__prefix__'),
            empty_permitted=True,
            use_required_attribute=False,
        )
        self.add_fields(form, None)
        return form


class PackedProductForm(SVForm):
    title = 'Products Used'
    product = forms.ModelChoiceField(Product.objects.none())
    quantity = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = (
            Product.objects.request_qs(self.request).select_related('product_type').filter(finished=False)
        )


PackedProductFormSet = forms.formset_factory(PackedProductForm, formset=SVBaseFormSet)
