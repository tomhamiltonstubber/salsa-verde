from django.conf import settings
from django.forms import DateTimeField, widgets

DT_OUTER_PICKER_HTML = """\
<div class="input-group date date-time-picker">
  {}
  <span class="input-group-text">
    <i class="fas fa-calendar"></i>
  </span>
</div>"""


class DateTimePicker(widgets.DateTimeInput):
    format = 'DD/MM/YYYY HH:MM'

    def __init__(self, field, start_empty=False, format='datetime'):
        self._is_datetime = False
        assert isinstance(field, DateTimeField)
        attrs = {'data-type': format, 'data-format': self.format}
        if start_empty:
            attrs['data-start-empty'] = 'true'
        formats = [settings.DT_FORMAT]
        self._is_datetime = True
        super().__init__(attrs, self.format)
        field.input_formats = formats

    def render(self, name, value, attrs=None, renderer=None):
        return DT_OUTER_PICKER_HTML.format(super().render(name, value, attrs=attrs, renderer=renderer))
