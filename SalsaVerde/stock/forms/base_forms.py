from datetime import date, datetime

from django import forms
from django.utils import timezone

from SalsaVerde.stock.widgets import DateTimePicker


class SVFormMixin:
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self._prepare_fields()
        # self.set_layout()

    def _prepare_fields(self):
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.DateTimeInput):
                field.widget = DateTimePicker(field)
            elif isinstance(field, forms.ModelChoiceField) and self.request:
                field.queryset = field.queryset.request_qs(self.request)

    def get_layout(self) -> list[list[tuple[forms.BoundField, int]]]:
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
            return organised_lines


class SVForm(SVFormMixin, forms.Form):
    pass


class SVModelForm(SVFormMixin, forms.ModelForm):
    full_width = False


def _date2datetime(date: date, day_end=False):
    """
    convert date to datetime in current timezone.

    :param date: datetime.date object
    :param day_end: if true 23.59.59 is used for the time
    :return: datetime.datetime object
    """
    if day_end:
        hours, mins, seconds = 23, 59, 59
    else:
        hours, mins, seconds = 0, 0, 0
    tzinfo = timezone.get_current_timezone()
    return datetime(date.year, date.month, date.day, hours, mins, seconds, tzinfo=tzinfo)


class SVFilterForm(SVFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fields_to_pop = []
        fields_to_add = {}
        for field_name, field in self.fields.items():
            field.required = False
            if isinstance(field, forms.DateTimeField):
                fields_to_pop.append(field_name)
                dt_field = forms.DateTimeField(required=False, label=field.label)
                fields_to_add[f'{field_name}_from'] = dt_field
                fields_to_add[f'{field_name}_to'] = dt_field
        for field_name in fields_to_pop:
            self.fields.pop(field_name)
        self.fields.update(fields_to_add)
        self._prepare_fields()

    def _prepare_fields(self):
        super()._prepare_fields()
        for _, field in self.fields.items():
            if isinstance(field.widget, forms.DateTimeInput):
                field.widget = DateTimePicker(field, start_empty=True)

    def filter_kwargs(self) -> dict:
        query_kwargs = {}
        for key, value in self.cleaned_data.items():
            value = value.strip() if isinstance(value, str) else value
            if value:
                if isinstance(value, date):
                    if key.endswith('date_from'):
                        query_kwargs[key[:-5] + '__gte'] = _date2datetime(value)
                    elif key.endswith('date_to'):
                        query_kwargs[key[:-3] + '__lte'] = _date2datetime(value, day_end=True)
                else:
                    query_kwargs[key] = value
        return query_kwargs
