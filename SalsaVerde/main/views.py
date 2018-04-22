from django.contrib.auth import user_logged_in
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.dispatch import receiver
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.main.base_views import AddModelView, UpdateModelView, DetailView, ListView, BasicView
from SalsaVerde.main.forms import (UpdateSupplierForm, UpdateUserForm, UpdateIngredientTypeForm, IngredientsFormSet,
                                   UpdateDocumentForm, UpdateProductTypeForm)
from SalsaVerde.main.models import User, Document, Ingredient, Supplier, IngredientType, ProductType


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
    form_class = UpdateUserForm
    model = User


user_add = UserAdd.as_view()


class UserEdit(UpdateModelView):
    form_class = UpdateUserForm
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
    form_class = UpdateSupplierForm


supplier_add = SupplierAdd.as_view()


class SupplierEdit(UpdateModelView):
    model = Supplier
    form_class = UpdateSupplierForm


supplier_edit = SupplierEdit.as_view()


class IngredientTypeList(ListView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]


ingredient_type_list = IngredientTypeList.as_view()


class IngredientTypeDetails(DetailView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]


ingredient_type_details = IngredientTypeDetails.as_view()


class IngredientTypeAdd(AddModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_add = IngredientTypeAdd.as_view()


class IngredientTypeEdit(UpdateModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_edit = IngredientTypeEdit.as_view()


class IngredientList(ListView):
    model = Ingredient
    display_items = [
        'ingredient_type',
        'batch_code',
        'intake_date',
        'supplier',
    ]

    def get_button_menu(self):
        return [
            ('Intake goods', reverse('intake-goods')),
            ('Ingredient types', reverse('ingredient-types')),
        ]


ingredient_list = IngredientList.as_view()


class IngredientDetails(DetailView):
    model = Ingredient
    display_items = [
        'ingredient_type',
        'batch_code',
        'intake_date',
        'condition',
        'supplier',
        'status',
        'quantity',
        'intake_document',
    ]

    def get_button_menu(self):
        return []


ingredient_details = IngredientDetails.as_view()


class IntakeGoods(AddModelView):
    model = Ingredient
    form_class = IngredientsFormSet
    template_name = 'intake_goods_form.jinja'
    title = 'Intake of goods'

    def form_valid(self, form):
        objects = form.save(commit=False)
        doc = Document.objects.create(
            author=self.request.user,
            type=Document.FORM_SUP01,
        )
        for object in objects:
            object.intake_user = self.request.user
            object.intake_document = doc
            object.save()
        return redirect(reverse('ingredients'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance')
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['forms'] = ctx.pop('form')
        return ctx


intake_goods = IntakeGoods.as_view()


class DocumentsList(ListView):
    model = Document
    display_items = [
        'type',
        'date_created',
        'author',
    ]


document_list = DocumentsList.as_view()


class DocumentDetails(DetailView):
    model = Document
    display_items = [
        'type',
        'date_created',
        'author',
        'file',
    ]


document_details = DocumentDetails.as_view()


class DocumentAdd(AddModelView):
    model = Document
    form_class = UpdateDocumentForm


document_add = DocumentAdd.as_view()


class DocumentEdit(UpdateModelView):
    model = Document
    form_class = UpdateDocumentForm


document_edit = DocumentEdit.as_view()


class ProductTypeList(ListView):
    model = ProductType
    display_items = [
        'name',
        'unit',
    ]


product_type_list = ProductTypeList.as_view()


class ProductTypeDetails(DetailView):
    model = ProductType
    display_items = [
        'name',
        'unit',
    ]


product_type_details = ProductTypeDetails.as_view()


class ProductTypeAdd(AddModelView):
    model = ProductType
    form_class = UpdateProductTypeForm


product_type_add = ProductTypeAdd.as_view()


class ProductTypeEdit(UpdateModelView):
    model = ProductType
    form_class = UpdateProductTypeForm


product_type_edit = ProductTypeEdit.as_view()


# class ProductAdd