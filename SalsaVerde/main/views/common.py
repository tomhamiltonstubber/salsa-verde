from django.contrib.auth import user_logged_in
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.main.models import Company, ProductType, IngredientType, ContainerType
from SalsaVerde.main.views.base_views import BasicView, ExtraContentView


class Index(BasicView):
    template_name = 'auth.jinja'
    title = 'Dashboard'


dashboard = Index.as_view()


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


class Setup(ExtraContentView):
    title = 'Setup'
    model = Company

    def extra_display_items(self):
        return [
            {
                'title': 'Product Types',
                'qs': ProductType.objects.request_qs(self.request),
                'fields': [
                    'name',
                    'ingredient_types',
                    'code',
                ],
                'add_url': reverse('product-types-add'),
            },
            {
                'title': 'Ingredient Types',
                'qs': IngredientType.objects.request_qs(self.request),
                'fields': [
                    'name',
                    'unit',
                ],
                'add_url': reverse('ingredient-types-add'),
            },
            {
                'title': 'Container Types',
                'qs': ContainerType.objects.request_qs(self.request),
                'fields': [
                    'name',
                    'size',
                    'type',
                ],
                'add_url': reverse('container-types-add'),
            },
        ]


setup = Setup.as_view()
