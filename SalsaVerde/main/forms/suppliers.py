from SalsaVerde.main.forms.base_forms import SVModelForm
from SalsaVerde.main.models import Supplier


class UpdateSupplierForm(SVModelForm):
    class Meta:
        model = Supplier
        exclude = {'company'}

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.request.user.company
        return super().save(commit)
