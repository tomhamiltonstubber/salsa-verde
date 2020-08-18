from SalsaVerde.stock.forms.base_forms import SVModelForm
from SalsaVerde.stock.models import User


class UpdateUserForm(SVModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'street', 'town', 'country', 'postcode', 'phone']

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.request.user.company
        return super().save(commit)
