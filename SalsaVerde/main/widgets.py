from django.conf import settings
from django.forms import DateTimeField, widgets

DT_OUTER_PICKER_HTML = """\
<div class="input-group date date-time-picker">
  {}
  <span class="input-group-addon">
    <i class="fa fa-calendar"></i>
  </span>
</div>"""


class DateTimePicker(widgets.DateTimeInput):
    format = 'DD/MM/YYYY HH:MM'

    def __init__(self, field):
        self._is_datetime = False
        assert isinstance(field, DateTimeField)
        attrs = {
            'data-type': 'datetime',
            'data-format': self.format,
            'data-minDate': '1900-01-01',
            'data-sideBySide': True,
        }
        formats = [settings.DT_FORMAT]
        self._is_datetime = True
        super().__init__(attrs, self.format)
        field.input_formats = formats

    def _data_value(self, value, format):
        if not value:
            return ''
        elif isinstance(value, str):
            if self._is_datetime:
                date, *time = value.split(' ')
                return date if '%Y' in format else ' '.join(time)
            else:
                return value
        else:
            return value.strftime(format)

    def render(self, name, value, attrs=None, renderer=None):
        attrs.update(
            {'data-date': self._data_value(value, '%Y-%m-%d'), 'data-time': self._data_value(value, '%H:%M'),}
        )
        return DT_OUTER_PICKER_HTML.format(super().render(name, value, attrs=attrs, renderer=renderer))
