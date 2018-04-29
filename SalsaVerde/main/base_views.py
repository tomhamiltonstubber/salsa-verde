import datetime

from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView, CreateView, UpdateView

from SalsaVerde import settings


def get_nav_menu():
    return [
        ('Dashboard', reverse('index')),
        ('Suppliers', reverse('suppliers')),
        ('Products', reverse('products')),
        ('Containers', reverse('containers')),
        ('Ingredients', reverse('ingredients')),
        ('Documents', reverse('documents')),
        ('Users', reverse('users')),
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
        return v or '–'

    def _display_label(self, item):
        display_funcs = {'display_', *self.display_funcs}
        if isinstance(item, tuple):
            return item[0]
        for func in display_funcs:
            item = item.replace(func, '')
        return self.model._meta.get_field(item).verbose_name

    def display_value(self, obj, item):
        if isinstance(item, tuple):
            return self._get_v(obj, item[1])
        else:
            return self._get_v(obj, item)

    def get_field_labels(self):
        return [self._display_label(item) for item in self.display_items]


class BasicView(DisplayHelpers, TemplateView):
    pass


def display_dt(dt):
    return dt.strftime(settings.DT_FORMAT)


class ListView(BasicView):
    template_name = 'list_view.jinja'
    model = None

    def get_button_menu(self):
        return [
            (f'Add new {self.model._meta.verbose_name}', reverse(f'{self.model.prefix()}-add'))
        ]

    def get_queryset(self):
        return self.model.objects.all()

    def get_field_data(self):
        for obj in self.get_queryset():
            yield obj.get_absolute_url(), [self.display_value(obj, f) for f in self.display_items]

    def get_title(self):
        return self.model._meta.verbose_name_plural

    def get_context_data(self, **kwargs):
        kwargs.update(
            field_names=self.get_field_labels(),
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


class UpdateModelView(FormView, UpdateView, ObjMixin):
    def get_title(self):
        return self.title or f'Edit %s' % self.object


class DetailView(ObjMixin, BasicView):
    template_name = 'details_view.jinja'
    model = None
    display_items = None

    def get_button_menu(self):
        return [
            ('All %s' % self.model._meta.verbose_name_plural, reverse(self.model.prefix())),
            ('Edit', reverse(f'{self.model.prefix()}-edit', kwargs={'pk': self.object.pk})),
        ]

    def get_title(self):
        return str(self.object)

    def get_display_items(self):
        return zip(self.get_field_labels(), [self.display_value(self.object, f) for f in self.display_items])

    def get_context_data(self, **kwargs):
        return super().get_context_data(display_items=self.get_display_items(), **kwargs)
