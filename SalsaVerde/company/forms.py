from SalsaVerde.company.models import Company
from SalsaVerde.stock.forms.base_forms import SVModelForm


class EditCompanyForm(SVModelForm):
    class Meta:
        fields = '__all__'
        model = Company
