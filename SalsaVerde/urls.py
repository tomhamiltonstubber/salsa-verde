from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path

from SalsaVerde.stock.models import (
    Container,
    ContainerType,
    Document,
    Ingredient,
    IngredientType,
    Product,
    ProductType,
    Supplier,
    User,
)
from SalsaVerde.stock.views.base_views import DeleteObjectView
from SalsaVerde.stock.views.common import dashboard, login, setup
from SalsaVerde.stock.views.containers import (
    change_container_status,
    container_type_add,
    container_type_details,
    container_type_edit,
    container_type_list,
    containers_details,
    containers_edit,
    containers_list,
    intake_containers,
)
from SalsaVerde.stock.views.documents import document_add, document_details, document_edit, document_list
from SalsaVerde.stock.views.ingredients import (
    change_ingredient_status,
    ingredient_details,
    ingredient_edit,
    ingredient_list,
    ingredient_type_add,
    ingredient_type_details,
    ingredient_type_edit,
    ingredient_type_list,
    intake_ingredients,
)
from SalsaVerde.stock.views.products import (
    change_product_status,
    product_add,
    product_bottle,
    product_details,
    product_edit,
    product_ingredient_add,
    product_list,
    product_size_type_add,
    product_size_type_delete,
    product_size_type_edit,
    product_type_add,
    product_type_details,
    product_type_edit,
    product_type_list,
    yield_container_add,
)
from SalsaVerde.stock.views.suppliers import supplier_add, supplier_details, supplier_edit, supplier_list
from SalsaVerde.stock.views.users import user_add, user_details, user_edit, user_list

user_patterns = [
    path('', user_list, name='users'),
    path('add/', user_add, name='users-add'),
    path('<int:pk>/', user_details, name='users-details'),
    path('<int:pk>/edit/', user_edit, name='users-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=User), name='users-delete'),
]

supplier_patterns = [
    path('', supplier_list, name='suppliers'),
    path('add/', supplier_add, name='suppliers-add'),
    path('<int:pk>/', supplier_details, name='suppliers-details'),
    path('<int:pk>/edit/', supplier_edit, name='suppliers-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Supplier), name='suppliers-delete'),
]

container_patterns = [
    path('', containers_list, name='containers'),
    path('intake-goods/containers/', intake_containers, name='intake-containers'),
    path('<int:pk>/', containers_details, name='containers-details'),
    path('<int:pk>/edit/', containers_edit, name='containers-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Container), name='containers-delete'),
    path('<int:pk>/status/', change_container_status, name='container-status'),
    path('types/', container_type_list, name='container-types'),
    path('types/add/', container_type_add, name='container-types-add'),
    path('types/<int:pk>/delete/', DeleteObjectView.as_view(model=ContainerType), name='container-types-delete'),
    path('types/<int:pk>/', container_type_details, name='container-types-details'),
    path('types/<int:pk>/edit/', container_type_edit, name='container-types-edit'),
]

ingredient_patterns = [
    path('', ingredient_list, name='ingredients'),
    path('<int:pk>/', ingredient_details, name='ingredients-details'),
    path('<int:pk>/edit', ingredient_edit, name='ingredients-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Ingredient), name='ingredients-delete'),
    path('<int:pk>/status/', change_ingredient_status, name='ingredient-status'),
    path('intake-goods/ingredients/', intake_ingredients, name='intake-ingredients'),
    path('types/', ingredient_type_list, name='ingredient-types'),
    path('types/add/', ingredient_type_add, name='ingredient-types-add'),
    path('types/<int:pk>/', ingredient_type_details, name='ingredient-types-details'),
    path('types/<int:pk>/edit/', ingredient_type_edit, name='ingredient-types-edit'),
    path('types/<int:pk>/delete/', DeleteObjectView.as_view(model=IngredientType), name='ingredient-types-delete'),
]

document_patterns = [
    path('', document_list, name='documents'),
    path('add/', document_add, name='documents-add'),
    path('<int:pk>/', document_details, name='documents-details'),
    path('<int:pk>/edit/', document_edit, name='documents-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Document), name='documents-delete'),
]

product_patterns = [
    path('', product_list, name='products'),
    path('add/', product_add, name='products-add'),
    path('<int:pk>/bottle/', product_bottle, name='products-bottle'),
    path('<int:pk>/', product_details, name='products-details'),
    path('<int:pk>/edit/', product_edit, name='products-edit'),
    path('<int:pk>/status/', change_product_status, name='product-status'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Product), name='products-delete'),
    path('<int:pk>/ingredients/add/', product_ingredient_add, name='product-ingredient-add'),
    path('<int:pk>/containers/add/', yield_container_add, name='yield-container-add'),
    path('types/', product_type_list, name='product-types'),
    path('types/add/', product_type_add, name='product-types-add'),
    path('types/<int:pk>/', product_type_details, name='product-types-details'),
    path('types/<int:pk>/edit/', product_type_edit, name='product-types-edit'),
    path('types/<int:pk>/delete/', DeleteObjectView.as_view(model=ProductType), name='product-types-delete'),
    path('types/size/<int:pk>/edit/', product_size_type_edit, name='product-type-sizes-edit'),
    path('types/size/<int:pk>/delete/', product_size_type_delete, name='product-type-sizes-delete'),
    path('types/<int:product_type>/size/add/', product_size_type_add, name='product-type-sizes-add'),
]

urlpatterns = [
    path('', dashboard, name='index'),
    path('login/', login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='base.jinja'), name='logout'),
    path('setup/', setup, name='setup'),
    path('ingredients/', include(ingredient_patterns)),
    path('products/', include(product_patterns)),
    path('containers/', include(container_patterns)),
    path('suppliers/', include(supplier_patterns)),
    path('documents/', include(document_patterns)),
    path('users/', include(user_patterns)),
    path('orders/', include('SalsaVerde.orders.urls')),
]


if settings.DEBUG:  # pragma: no cover
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
