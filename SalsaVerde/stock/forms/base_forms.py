from django import forms

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
        if hasattr(self, 'Meta') and (layout := getattr(self.Meta, 'layout', None)):
            organised_lines = []
            for line in layout:
                organised_line = []
                defined_widths = [field_name[1] for field_name in line if isinstance(field_name, tuple)]
                width_leftover = 12 - sum(defined_widths)
                width_per_undefined_item = width_leftover / (len(line) - len(defined_widths))
                for field_name in line:
                    if isinstance(field_name, str):
                        field = self.fields[field_name].get_bound_field(self, field_name)
                        width = width_per_undefined_item
                    else:
                        field = self.fields[field_name[0]].get_bound_field(self, field_name[0])
                        width = field_name[1]
                    organised_line.append((field, int(width)))
                organised_lines.append(organised_line)
            self.layout = organised_lines


class SVForm(SVFormMixin, forms.Form):
    pass


class SVModelForm(SVFormMixin, forms.ModelForm):
    full_width = False
