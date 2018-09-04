from django.contrib.auth import user_logged_in
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .base_views import UpdateModelView, AddModelView, DetailView, ListView, BasicView
from SalsaVerde.main.forms import UpdateUserForm
from SalsaVerde.main.models import Document, User


class Login(LoginView):
    template_name = 'login.jinja'
    title = 'Login'
    form_class = AuthenticationForm
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


class Index(BasicView):
    template_name = 'auth.jinja'
    title = 'Dashboard'


dashboard = Index.as_view()


class UserList(ListView):
    model = User
    display_items = [
        'email',
        'first_name',
        'last_name',
        'last_logged_in',
    ]


user_list = UserList.as_view()


class UserDetails(DetailView):
    model = User
    display_items = [
        'email',
        ('Name', 'name'),
        ('Address', 'address'),
        'last_logged_in',
    ]

    def extra_display_items(self):
        return [
            {
                'title': 'Authored Documents',
                'qs': Document.objects.request_qs(self.request).filter(author=self.object),
                'fields': [
                    ('Document', 'name'),
                    'date_created',
                ],
            },
            {
                'title': 'Associated Documents',
                'qs': Document.objects.request_qs(self.request).filter(focus=self.object),
                'fields': [
                    ('Document', 'name'),
                    'date_created',
                ],
                'add_url': reverse('documents-add') + f'?focus={self.object.pk}'
            },
        ]


user_details = UserDetails.as_view()


class UserAdd(AddModelView):
    form_class = UpdateUserForm
    model = User


user_add = UserAdd.as_view()


class UserEdit(UpdateModelView):
    form_class = UpdateUserForm
    model = User


user_edit = UserEdit.as_view()
