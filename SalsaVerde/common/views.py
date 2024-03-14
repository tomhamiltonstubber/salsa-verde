import datetime
from functools import partial
from typing import Iterator

from django.conf import settings
from django.contrib.auth import user_logged_in
from django.contrib.auth.views import LoginView
from django.db.models import QuerySet
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, redirect
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import CreateView, FormView, ListView as DjListView, TemplateView, UpdateView

from SalsaVerde.common.forms import AuthForm


class QuerySetMixin:
    order_by = None

    def get_queryset(self):
        if self.request.user.is_authenticated:
            qs = self.model.objects.request_qs(self.request)
            if self.order_by:
                qs = qs.order_by(self.order_by)
            return qs
        return self.model.objects.none()


VIEW_FUNC = 'func|'
OBJ_URL = 'obj_url|'


class DisplayHelpers:
    title = None
    display_items = None
    display_funcs = {VIEW_FUNC, OBJ_URL}

    def get_title(self):
        return mark_safe(self.title)

    def get_display_items(self):
        return self.display_items

    def get_context_data(self, **kwargs) -> dict:
        return super().get_context_data(
            nav_links=get_nav_menu(self.request),
            title=self.get_title(),
            button_menu=self.process_button_menu(self.get_button_menu()),
            **kwargs,
        )

    def _object_url(self, rurl):
        try:
            return reverse(rurl)
        except NoReverseMatch as e:
            if getattr(self, 'object', False):  # pragma: no cover
                return reverse(rurl, kwargs={'pk': self.object.pk})
            raise e

    def get_button_menu(self):
        return []

    def process_button_menu(self, buttons) -> list:
        btns = []
        for button in buttons:
            data = button.get('data', {})
            if 'rurl' in button:
                button['url'] = self._object_url(button.pop('rurl'))
            for f in ('confirm', 'method'):
                if f in button:
                    data[f] = button.pop(f)
                if data:
                    button['data'] = data
            if not button.get('group'):
                button['group'] = 1
            btns.append(button)
        return btns

    def _get_attr(self, obj, attr_name):
        for b in attr_name.split('__'):
            if obj:
                obj = getattr(obj, b)
        return obj

    def _get_v(self, obj, field):
        if hasattr(obj, f'display_{field}'):
            return getattr(obj, f'display_{field}')()
        elif field.startswith(VIEW_FUNC):
            field = field.replace(VIEW_FUNC, '')
            return getattr(self, field)(obj)
        elif field.startswith(OBJ_URL):
            field = field.replace(OBJ_URL, '')
            related_obj = self._get_attr(obj, field)
            if related_obj:
                return mark_safe(f'<a href="{related_obj.get_absolute_url()}">{related_obj}</a>')
            return '–'
        attr = self._get_attr(obj, field)
        if isinstance(attr, partial) or callable(attr):
            v = attr()
        else:
            v = attr
        if isinstance(v, datetime.datetime):
            return display_dt(v)
        elif v is True:
            return mark_safe('<span class="fa fa-check"></span')
        elif v is False:
            return mark_safe('<span class="fa fa-times"></span')
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
        return [self.display_value(obj, f) for f in (display_items or [])]

    def get_display_labels(self, display_items, obj=None):
        return [self._display_label(item, obj) for item in (display_items or [])]


class BasicView(DisplayHelpers, TemplateView):
    pass


class ModelBasicView(BasicView):
    pass


class Index(ModelBasicView):
    template_name = 'auth.jinja'
    title = 'Dashboard'


dashboard = Index.as_view()


class Login(LoginView):
    template_name = 'login.jinja'
    title = 'Login'
    form_class = AuthForm
    redirect_authenticated_user = True

    def get_redirect_url(self):
        return reverse('index')

    def get_context_data(self, **kwargs):
        return super().get_context_data(title=self.title, **kwargs)


login = Login.as_view()


@receiver(user_logged_in)
def update_user_history(sender, user, **kwargs):
    user.last_logged_in = timezone.now()
    user.save(update_fields=['last_logged_in'])


def get_nav_menu(request):
    active_path = request.path.split('/')
    return [
        ('Orders', 'store', reverse('orders-list'), 'orders' in active_path),
        ('Products', 'bottle-droplet', reverse('products'), 'products' in active_path),
        ('Packaging', 'jar', reverse('containers'), 'containers' in active_path),
        ('Suppliers', 'tractor', reverse('suppliers'), 'suppliers' in active_path),
        ('Raw Ingredients', 'apple-whole', reverse('ingredients'), 'ingredients' in active_path),
        # ('Documents', 'document', reverse('documents'), 'documents' in active_path),
        ('Users', 'user', reverse('users'), 'users' in active_path),
        ('Setup', 'gear', reverse('setup'), 'setup' in active_path),
    ]


class FieldInfo:
    field = None
    verbose_name = None


def display_dt(dt):
    return dt.strftime(settings.DT_FORMAT)


class ModelListView(QuerySetMixin, DisplayHelpers, DjListView):
    template_name = 'list_view.jinja'
    model = None
    filter_form = None
    filter_info = None
    paginate_by = 40

    @cached_property
    def _mutable_get_args(self):
        """
        Returns a mutable copy of the GET args so that we can use them to render the filtered form, and pass them into
        the view so that pagination works with filters.
        """
        args = self.request.GET.copy()
        args._mutable = True
        args.pop('page', None)
        query_params = {}
        for key, value in args.lists():
            if not value or value == ['']:
                continue
            if len(value) > 1:
                query_params[key] = value
            else:
                query_params[key] = value[0]
        return query_params

    @cached_property
    def _propped_filter_form(self):
        # Only want to render the search form if we need to.
        if self.filter_form and self._mutable_get_args:
            return self.filter_form(request=self.request, data=self.request.GET)

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        if self._propped_filter_form:
            self._propped_filter_form.full_clean()
            if self._propped_filter_form.is_valid():
                return qs.filter(**self._propped_filter_form.filter_kwargs()).distinct()
            else:
                return self.model.objects.none()
        else:
            return qs

    def get_button_menu(self):
        yield {'name': f'Add new {self.model._meta.verbose_name}', 'url': reverse(f'{self.model.prefix()}-add')}

    def get_field_data(self, object_list: list) -> Iterator[tuple[str, list]]:
        for obj in object_list:
            yield obj.get_absolute_url(), self.get_display_values(obj, self.get_display_items())

    def get_title(self):
        return self.model._meta.verbose_name_plural

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.filter_form:
            filter_form = self.filter_form(request=self.request, data=self._mutable_get_args)
            filter_form.set_layout()
            ctx.update(
                filter_form=filter_form,
                start_filter_form_open=self._propped_filter_form and self._propped_filter_form.filter_kwargs(),
            )
        ctx.update(
            field_names=self.get_display_labels(self.get_display_items()),
            field_data=list(self.get_field_data(ctx['object_list'])),
        )
        return ctx


class ObjMixin:
    def dispatch(self, request, *args, **kwargs):
        self.object = self.model.objects.get(pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class _SVFormView(DisplayHelpers):
    template_name = 'form_view.jinja'
    cancel_url = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(request=self.request)
        return kwargs

    def get_cancel_url(self):
        return self.cancel_url


class SVModelFormView(_SVFormView, DisplayHelpers):
    model = NotImplemented


class SVFormView(_SVFormView, DisplayHelpers, FormView):
    pass


class AddModelView(SVModelFormView, CreateView):
    cancel_url = None

    def get_title(self):
        return self.title or f'Create new {self.model._meta.verbose_name}'

    def get_cancel_url(self) -> str:
        if hasattr(self.model, 'prefix'):
            return reverse(self.model.prefix())
        else:
            raise NotImplementedError


class UpdateModelView(QuerySetMixin, SVModelFormView, UpdateView, ObjMixin):
    def get_title(self):
        return self.title or f'Edit {self.object}'

    def get_cancel_url(self):
        return self.cancel_url or self.object.get_absolute_url()


class ExtraContentView(ModelBasicView):
    template_name = 'details_view.jinja'

    def extra_display_items(self):
        return {}

    @staticmethod
    def get_absolute_url(obj):
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()

    def _get_extra_content(self):
        for item in self.extra_display_items():
            if item['qs'].exists():
                objects = list(item['qs'])[:20]
                yield {
                    'title': item['title'],
                    'field_names': self.get_display_labels(item['fields'], obj=item['qs'][0]),
                    'field_vals': [
                        (self.get_absolute_url(obj), self.get_display_values(obj, item['fields'])) for obj in objects
                    ],
                    'add_url': item.get('add_url'),
                    'icon': item.get('icon'),
                }
            elif item.get('add_url'):
                yield {'title': item['title'], 'add_url': item['add_url']}

    def get_context_data(self, **kwargs):
        return super().get_context_data(extra_content=self._get_extra_content(), **kwargs)


class DetailView(ObjMixin, ExtraContentView):
    model = None

    def get_title(self):
        return str(self.object)

    def get_button_menu(self):
        return [
            {
                'name': f'Back to all {self.model._meta.verbose_name_plural}',
                'url': reverse(self.model.prefix()),
                'icon': 'fa-arrow-left',
                'group': 1,
            },
            {
                'name': 'Edit',
                'url': reverse(f'{self.model.prefix()}-edit', kwargs={'pk': self.object.pk}),
                'icon': 'fa-edit',
                'group': 2,
            },
            {
                'name': 'Delete',
                'confirm': f'Are you sure you want to delete this {self.model._meta.verbose_name}?',
                'rurl': f'{self.model.prefix()}-delete',
                'method': 'POST',
                'icon': 'fa-trash',
                'group': 2,
            },
        ]

    def get_context_data(self, **kwargs):
        display_vals = self.get_display_values(self.object, self.get_display_items())
        display_labels = self.get_display_labels(self.get_display_items())
        return super().get_context_data(display_items=zip(display_labels, display_vals), **kwargs)


class DeleteObjectView(View):
    model = NotImplemented
    http_method_names = ['post']
    redirect_view = None

    def get_redirect_view(self):
        return self.model.prefix()

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model.objects.request_qs(request), pk=kwargs['pk'])
        obj.delete()
        return redirect(self.get_redirect_view())
