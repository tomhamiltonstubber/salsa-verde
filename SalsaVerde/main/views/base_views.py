import datetime

from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.views import View
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
        ('Setup', reverse('setup')),
        ('Logout', reverse('logout')),
    ]


class FieldInfo:
    field = None
    verbose_name = None


class DisplayHelpers:
    title = None
    display_items = None
    display_funcs = {'func|'}

    def get_title(self):
        return mark_safe(self.title)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            nav_links=get_nav_menu(),
            title=self.get_title(),
            button_menu=self.process_button_menu(),
            **kwargs
        )

    def _object_url(self, rurl):
        try:
            return reverse(rurl)
        except NoReverseMatch as e:
            if getattr(self, 'object', False):
                return reverse(rurl, kwargs={'pk': self.object.pk})
            raise e

    def get_button_menu(self):
        return []

    def process_button_menu(self):
        for button in self.get_button_menu():
            data = button.get('data', {})
            if 'rurl' in button:
                button['url'] = self._object_url(button.pop('rurl'))
            for f in ('confirm', 'method'):
                if f in button:
                    data[f] = button.pop(f)
                if data:
                    button['data'] = data
            yield button

    def _get_attr(self, obj, attr_name):
        for b in attr_name.split('__'):
            if obj:
                obj = getattr(obj, b)
        return obj

    def _get_v(self, obj, field):
        get_func = False
        if hasattr(obj, f'display_{field}'):
            return getattr(obj, f'display_{field}')()
        elif field.startswith('func|'):
            field = field.replace('func|', '')
            return getattr(self, field)(obj)
        attr = self._get_attr(obj, field)
        v = attr(obj) if get_func else attr
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
        for i in item.split('__'):
            field = model._meta.get_field(i)
            if field.remote_field:
                model = field.remote_field.model
        return field.verbose_name

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


class ExtraContentView(BasicView):
    template_name = 'details_view.jinja'

    def extra_display_items(self):
        return {}

    @staticmethod
    def get_absolute_url(obj):
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()
        return

    def _get_extra_content(self):
        for item in self.extra_display_items():
            if item['qs'].exists():
                yield {
                    'title': item['title'],
                    'field_names': self.get_display_labels(item['fields'], obj=item['qs'][0]),
                    'field_vals': [
                        (self.get_absolute_url(obj), self.get_display_values(obj, item['fields'])) for obj in item['qs']
                    ],
                    'add_url': item.get('add_url'),
                }
            elif item.get('add_url'):
                yield {'title': item['title'], 'add_url': item['add_url']}

    def get_context_data(self, **kwargs):
        return super().get_context_data(extra_content=self._get_extra_content(), **kwargs)


class DetailView(ObjMixin, ExtraContentView):
    model = None
    display_items = None

    def get_title(self):
        return str(self.object)

    def get_button_menu(self):
        return [
            {'name': 'All %s' % self.model._meta.verbose_name_plural, 'url': reverse(self.model.prefix())},
            {'name': 'Edit', 'url': reverse(f'{self.model.prefix()}-edit', kwargs={'pk': self.object.pk})},
            {
                'name': 'Delete',
                'confirm': 'Are you sure you want to delete this %s?' % self.model._meta.verbose_name,
                'rurl': f'{self.model.prefix()}-delete',
                'method': 'POST',
            },
        ]

    def get_context_data(self, **kwargs):
        display_vals = self.get_display_values(self.object, self.display_items)
        display_labels = self.get_display_labels(self.display_items)
        return super().get_context_data(display_items=zip(display_labels, display_vals), **kwargs)


class SVFormsetForm:
    formset_classes = {'formset': NotImplemented}
    request = None
    success_url = NotImplemented

    def get_success_url(self):
        return self.success_url

    def form_valid(self, form):
        self.object = None
        for formset_class in self.formset_classes.values():
            formset = formset_class(self.request.POST)
            formset.full_clean()
            if formset.is_valid():
                self.object = self.object or form.save()
                formset.instance = self.object
                formset.save()
            else:
                return self.form_invalid(form)
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        assert not self.object, 'This form is for adding objects only because formsets are shite.'
        for name, formset_class in self.formset_classes.items():
            if self.request.POST:
                formset = formset_class(self.request.POST)
            else:
                formset = formset_class()
            ctx[name] = formset
        return ctx


class DeleteObjectView(View):
    model = NotImplemented
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model.objects.request_qs(request), pk=kwargs['pk'])
        obj.delete()
        return redirect(self.model.prefix())
