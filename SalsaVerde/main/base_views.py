import datetime

from django.urls import reverse
from django.views.generic import TemplateView, CreateView, UpdateView


class BasicView(TemplateView):
    title = None

    def get_nav_menu(self):
        return [
            ('Users', reverse('users')),
            ('Suppliers', reverse('suppliers')),
        ]

    def get_button_menu(self):
        return []

    def get_title(self):
        return self.title

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            nav_links=self.get_nav_menu(),
            title=self.get_title(),
            button_menu=self.get_button_menu(),
            **kwargs
        )


def display_value(obj, field):
    v = getattr(obj, field)
    if isinstance(v, datetime.datetime):
        return v.strftime('%d/%m/%Y %H:%M')
    return v


class ListView(BasicView):
    model = None
    display_items = None
    template_name = 'list_view.jinja'

    def get_button_menu(self):
        return [
            (f'Add new {self.model._meta.verbose_name}', reverse(f'{self.model.prefix()}-add'))
        ]

    def get_field_names(self):
        return [self.model._meta.get_field(f).verbose_name for f in self.display_items]

    def get_queryset(self):
        return self.model.objects.all()

    def get_field_data(self):
        qs = self.get_queryset()
        for obj in qs:
            yield obj.get_absolute_url(), [display_value(obj, f) for f in self.display_items]

    def get_title(self):
        return self.model._meta.verbose_name_plural

    def get_context_data(self, **kwargs):
        kwargs.update(
            field_names=self.get_field_names(),
            field_data=self.get_field_data(),
            add_url=reverse(f'{self.model.prefix()}-add'),
        )
        return super().get_context_data(**kwargs)


class ObjMixin:
    def dispatch(self, request, *args, **kwargs):
        self.object = self.model.objects.get(pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class ModelFormMixin:
    model = None
    template_name = 'form_view.jinja'

    def __init__(self):
        super().__init__()
        self.fields = self.model.model_form_fields()


class AddModelView(ModelFormMixin, CreateView):
    def get_success_url(self):
        return reverse(self.model.prefix())

    def get_context_data(self, **kwargs):
        return super().get_context_data(title='Create new %s' % self.model._meta.verbose_name, **kwargs)


class UpdateModelView(ModelFormMixin, UpdateView, ObjMixin):
    def get_success_url(self):
        return reverse(f'{self.model.prefix()}-details', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        return super().get_context_data(title=f'Edit %s' % self.object, **kwargs)


class DetailView(ObjMixin, BasicView):
    template_name = 'details_view.jinja'
    model = None
    display_items = None

    def get_button_menu(self):
        return [
            ('Edit', reverse(f'{self.model.prefix()}-edit', kwargs={'pk': self.object.pk}))
        ]

    def get_title(self):
        return str(self.object)

    def get_display_items(self):
        field_names = [self.model._meta.get_field(f).verbose_name for f in self.display_items]
        return zip(field_names, [display_value(self.object, f) for f in self.display_items])

    def get_context_data(self, **kwargs):
        return super().get_context_data(display_items=self.get_display_items(), **kwargs)
