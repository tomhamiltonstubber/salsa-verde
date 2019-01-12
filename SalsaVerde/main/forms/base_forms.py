from django import forms

from SalsaVerde.main.models import Ingredient, GoodsIntake, Document
from SalsaVerde.main.widgets import DateTimePicker


class SVModelForm(forms.ModelForm):
    full_width = False

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.DateTimeInput):
                self.fields[field].widget = DateTimePicker(self.fields[field])
            if isinstance(self.fields[field], forms.ModelChoiceField) and self.request:
                self.fields[field].queryset = self.fields[field].queryset.request_qs(self.request)


class EmptyQSFormSet(forms.BaseModelFormSet):
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return Ingredient.objects.none()


class GoodsIntakeForm(SVModelForm):
    class Meta:
        model = GoodsIntake
        exclude = {'date_created'}

    def __init__(self, document_type, *args, **kwargs):
        self.document_type = document_type
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit)
        if not obj.documents.exists():
            Document.objects.create(author=self.request.user, type=self.document_type, goods_intake=obj)
        return obj
