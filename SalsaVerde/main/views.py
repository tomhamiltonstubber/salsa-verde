from django.contrib.auth import user_logged_in
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from SalsaVerde.main.models import User


class Login(LoginView):
    template_name = 'login.html'
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
    user.save()


class BasicView(TemplateView):
    title = None

    def get_context_data(self, **kwargs):
        nav_links = [reverse(l) for l in ['users']]
        return super().get_context_data(nav_links=nav_links, title=self.title, **kwargs)


class Index(BasicView):
    template_name = 'auth.html'
    title = 'Dashboard'


dashboard = Index.as_view()


class ListView(BasicView):
    model = None
    display_items = None
    template_name = 'list_view.html'

    def get_field_names(self):
        return [self.model._meta.get_field(f).verbose_name for f in self.display_items]

    def get_items(self):
        return self.model.objects.values_list(*self.display_items)

    def get_context_data(self, **kwargs):
        return super().get_context_data(field_names=self.get_field_names(), items=self.get_items(), **kwargs)


class UserList(ListView):
    model = User
    display_items = [
        'email',
        'first_name',
        'last_name',
        'last_logged_in',
    ]


user_list = UserList.as_view()
