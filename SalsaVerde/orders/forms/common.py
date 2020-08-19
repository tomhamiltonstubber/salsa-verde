from django import forms

from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.stock.forms.base_forms import SVForm


class PackageForm(SVForm):
    title = 'Packages sending'

    package_type = forms.ModelChoiceField(PackageTemplate.objects.none(), required=False)
    length = forms.DecimalField(label='Length (cm)', decimal_places=1, min_value=0)
    width = forms.DecimalField(label='Width (cm)', decimal_places=1, min_value=0)
    height = forms.DecimalField(label='Height (cm)', decimal_places=1, min_value=0)
    weight = forms.DecimalField(label='Weight (kg)', decimal_places=2, min_value=0)


PackageFormSet = forms.formset_factory(PackageForm)
