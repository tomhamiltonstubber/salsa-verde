from django.shortcuts import get_object_or_404

from SalsaVerde.main.forms.base_forms import SVModelForm
from SalsaVerde.main.models import Document, Supplier, User


class UpdateDocumentForm(SVModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['author'].initial = self.request.user
            self.fields['file'].required = False
        if self.request.GET.get('supplier'):
            sup = get_object_or_404(Supplier.objects.request_qs(self.request), pk=self.request.GET['supplier'])
            self.fields['supplier'].initial = sup
        if self.request.GET.get('focus'):
            user = get_object_or_404(User.objects.request_qs(self.request), pk=self.request.GET['focus'])
            self.fields['focus'].initial = user

    class Meta:
        model = Document
        exclude = {'edits', 'date_created'}
