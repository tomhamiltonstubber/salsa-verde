from django.contrib.auth import user_logged_in
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.main.base_views import AddModelView, UpdateModelView, DetailView, ListView, BasicView
from SalsaVerde.main.forms import (UpdateSupplierForm, UpdateUserForm, UpdateDocumentForm, UpdateProductTypeForm,
                                   UpdateProductForm, ProductIngredientFormSet, YieldContainersFormSet)
from SalsaVerde.main.models import User, Document, Supplier, ProductType, Product


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
        'main_contact',
        'phone',
        'email',
    ]


supplier_list = SupplierList.as_view()


class SupplierDetails(DetailView):
    model = Supplier
    display_items = [
        'name',
        ('Address', 'address'),
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
        'ingredient_types',
    ]


product_type_list = ProductTypeList.as_view()


class ProductTypeDetails(DetailView):
    model = ProductType
    display_items = [
        ('Ingredient Types', 'func|ingredient_types_display'),
    ]

    def ingredient_types_display(self, obj):
        return ', '.join(obj.ingredient_types.values_list('name', flat=True).order_by('name'))


product_type_details = ProductTypeDetails.as_view()


class ProductTypeAdd(AddModelView):
    model = ProductType
    form_class = UpdateProductTypeForm


product_type_add = ProductTypeAdd.as_view()


class ProductTypeEdit(UpdateModelView):
    model = ProductType
    form_class = UpdateProductTypeForm


product_type_edit = ProductTypeEdit.as_view()


class ProductList(ListView):
    model = Product
    display_items = [
        'product_type',
        'date_of_infusion',
        'date_of_bottling',
        'date_of_best_before',
        'yield_quantity',
    ]

    def get_button_menu(self):
        return [
            ('Add Product', reverse('products-add')),
            ('Product Types', reverse('product-types')),
        ]


product_list = ProductList.as_view()


class ProductAdd(AddModelView):
    model = Product
    form_class = UpdateProductForm
    template_name = 'add_product_form.jinja'

    def form_valid(self, form):
        product_ingredient_formset = ProductIngredientFormSet(self.request.POST)
        yield_container_formset = YieldContainersFormSet(self.request.POST)
        obj = form.save()
        if product_ingredient_formset.is_valid():
            product_ingredient_formset.instance = obj
            product_ingredient_formset.save()
        if yield_container_formset.is_valid():
            yield_container_formset.instance = obj
            yield_container_formset.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            product_ingredient_forms=ProductIngredientFormSet(),
            yield_container_forms=YieldContainersFormSet(),
            **kwargs
        )


product_add = ProductAdd.as_view()


class ProductEdit(ProductAdd, UpdateModelView):
    model = Product
    form_class = UpdateProductForm
    template_name = 'add_product_form.jinja'

    def get_context_data(self, **kwargs):
        return super().get_context_data(product_ingredient_forms=ProductIngredientFormSet, **kwargs)


product_edit = ProductEdit.as_view()


class ProductDetails(DetailView):
    model = Product
    display_items = [
        'product_type',
        'date_of_infusion',
        'date_of_bottling',
        'date_of_best_before',
        'yield_quantity',
    ]


product_details = ProductDetails.as_view()
