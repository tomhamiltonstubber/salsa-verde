from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.stock.forms.base_forms import SVModelForm


class UpdatePackageTemplateForm(SVModelForm):
    class Meta:
        model = PackageTemplate
        exclude = {'company'}

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.request.user.company
        return super().save(commit)
