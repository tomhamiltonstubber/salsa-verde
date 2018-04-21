from django.contrib.auth import user_logged_in
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.main.base_views import AddModelView, UpdateModelView, DetailView, ListView, BasicView
from SalsaVerde.main.models import User, Document, Ingredient, Supplier


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
    user.save()


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
        'first_name',
        'last_name',
        'last_logged_in',
    ]

    def get_context_data(self, **kwargs):
        kwargs.update(
            authored_doc_qs=Document.objects.filter(author=self.object),
            focussed_doc_qs=Document.objects.filter(focus=self.object),
        )
        return super().get_context_data(**kwargs)


user_details = UserDetails.as_view()


class UserAdd(AddModelView):
    model = User


user_add = UserAdd.as_view()


class UserEdit(UpdateModelView):
    model = User


user_edit = UserEdit.as_view()


class SupplierList(ListView):
    model = Supplier
    display_items = [
        'name',
        'street',
        'town',
        'main_contact',
        'postcode',
        'phone',
        'email',
    ]


supplier_list = SupplierList.as_view()


class SupplierDetails(DetailView):
    model = Supplier
    display_items = [
        'name',
        'street',
        'town',
        'country',
        'postcode',
        'phone',
        'email',
    ]


supplier_details = SupplierDetails.as_view()


class SupplierAdd(AddModelView):
    model = Supplier


supplier_add = SupplierAdd.as_view()


class SupplierEdit(UpdateModelView):
    model = Supplier


supplier_edit = SupplierEdit.as_view()


class IngredientList(ListView):
    model = Ingredient
    display_items = [
        'ingredient_type',
        'batch_code',
        'intake_date',
        'supplier',
    ]

