import datetime

from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView, CreateView, UpdateView


def get_nav_menu():
    return [
        ('Dashboard', reverse('index')),
        ('Products', reverse('products')),
        ('Suppliers', reverse('suppliers')),
        ('Containers', reverse('containers')),
        ('Ingredients', reverse('ingredients')),
        ('Documents', reverse('documents')),
        ('Users', reverse('users')),
        ('Logout', reverse('logout')),
    ]


class FieldInfo:
    field = None
    verbose_name = None


class DisplayHelpers:
    title = None
    display_items = None
    display_funcs = {'func|', 'abs|'}

    def get_title(self):
        return mark_safe(self.title)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            nav_links=get_nav_menu(),
            title=self.get_title(),
            button_menu=self.get_button_menu(),
            **kwargs
        )

    def get_button_menu(self):
        return []

    def _get_attr(self, obj, attr_name):
        for b in attr_name.split('__'):
            if obj:
                obj = getattr(obj, b)
        return obj

    def _get_v(self, obj, field):
        get_abs = False
        get_func = False
        if hasattr(obj, f'display_{field}'):
            return getattr(obj, f'display_{field}')()
        elif field.startswith('abs|'):
            field = field.replace('abs|', '')
            get_abs = True
        elif field.startswith('func|'):
            field = field.replace('func|', '')
            return getattr(self, field)(obj)
        attr = self._get_attr(obj, field)
        if get_abs:
            v = mark_safe(f'<a href="{attr.get_absolute_url()}">{attr}</a>')
        elif get_func:
            v = attr(obj)
        else:
            v = attr
        if isinstance(v, datetime.datetime):
            return display_dt(v)
        elif v is True:
            return mark_safe(f'<span class="fa fa-check"></span')
        elif v is False:
            return mark_safe(f'<span class="fa fa-times"></span')
        return v or '–'

    def _display_label(self, item, obj):
        display_funcs = {'display_', *self.display_funcs}
        if isinstance(item, tuple):
            return item[0]
        for func in display_funcs:
            item = item.replace(func, '')
        model = obj and type(obj) or self.model
        return model._meta.get_field(item).verbose_name

    def display_value(self, obj, item):
        if isinstance(item, tuple):
            return self._get_v(obj, item[1])
        else:
            return self._get_v(obj, item)

    def get_display_values(self, obj, display_items):
        return [self.display_value(obj, f) for f in display_items]

    def get_display_labels(self, display_items, obj=None):
        return [self._display_label(item, obj) for item in display_items]


class QuerySetMixin:
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.model.objects.request_qs(self.request)
        return self.model.objects.none()


class BasicView(QuerySetMixin, DisplayHelpers, TemplateView):
    pass


def display_dt(dt):
    return dt.strftime(settings.DT_FORMAT)


class ListView(BasicView):
    template_name = 'list_view.jinja'
    model = None

    def get_button_menu(self):
        return [
            {'name': f'Add new {self.model._meta.verbose_name}', 'url': reverse(f'{self.model.prefix()}-add')}
        ]

    def get_field_data(self):
        for obj in self.get_queryset():
            yield obj.get_absolute_url(), self.get_display_values(obj, self.display_items)

    def get_title(self):
        return self.model._meta.verbose_name_plural

    def get_context_data(self, **kwargs):
        kwargs.update(
            field_names=self.get_display_labels(self.display_items),
            field_data=self.get_field_data(),
        )
        return super().get_context_data(**kwargs)


class ObjMixin:
    def dispatch(self, request, *args, **kwargs):
        self.object = self.model.objects.get(pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class FormView(DisplayHelpers):
    template_name = 'form_view.jinja'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(request=self.request)
        return kwargs


class AddModelView(FormView, CreateView):
    def get_title(self):
        return self.title or 'Create new %s' % self.model._meta.verbose_name


class UpdateModelView(QuerySetMixin, FormView, UpdateView, ObjMixin):
    def get_title(self):
        return self.title or f'Edit %s' % self.object


class DetailView(ObjMixin, BasicView):
    template_name = 'details_view.jinja'
    model = None
    display_items = None

    def get_button_menu(self):
        return [
            {'name': 'All %s' % self.model._meta.verbose_name_plural, 'url': reverse(self.model.prefix())},
            {'name': 'Edit', 'url': reverse(f'{self.model.prefix()}-edit', kwargs={'pk': self.object.pk})},
        ]

    def get_title(self):
        return str(self.object)

    def extra_display_items(self):
        return {}

    def get_extra_content(self):
        for item in self.extra_display_items():
            if item['qs'].exists():
                yield {
                    'title': item['title'],
                    'field_names': self.get_display_labels(item['fields'], obj=item['qs'][0]),
                    'field_vals': [
                        (obj.get_absolute_url(), self.get_display_values(obj, item['fields'])) for obj in item['qs']
                    ],
                    'add_url': item.get('add_url'),
                }
            elif item.get('add_url'):
                yield {'title': item['title'], 'add_url': item['add_url']}

    def get_context_data(self, **kwargs):
        display_vals = self.get_display_values(self.object, self.display_items)
        display_labels = self.get_display_labels(self.display_items)
        return super().get_context_data(
            display_items=zip(display_labels, display_vals),
            extra_content=self.get_extra_content(),
            **kwargs
        )
