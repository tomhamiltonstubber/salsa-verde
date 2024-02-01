from django import forms

from SalsaVerde.stock.models import Document, GoodsIntake
from SalsaVerde.stock.widgets import DateTimePicker


class SVFormMixin:
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.DateTimeInput):
                self.fields[field].widget = DateTimePicker(self.fields[field])
            if isinstance(self.fields[field], forms.ModelChoiceField) and self.request:
                self.fields[field].queryset = self.fields[field].queryset.request_qs(self.request)
        if layout := getattr(self.Meta, 'layout', None):
            organised_fields = []
            for line in layout:
                defined_widths = [item[1] for item in line if isinstance(item, tuple)]
                line = [
                    (
                        self.fields[item].get_bound_field(self, item),
                        int((12 - sum(defined_widths)) / (len(line) - len(defined_widths)))
                        if isinstance(item, str)
                        else item[1],
                    )
                    for item in line
                ]
                organised_fields.append(line)
            self.layout = organised_fields


class SVForm(SVFormMixin, forms.Form):
    pass


class SVModelForm(SVFormMixin, forms.ModelForm):
    full_width = False


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
