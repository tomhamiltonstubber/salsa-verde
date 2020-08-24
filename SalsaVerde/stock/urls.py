from django.urls import include, path

from SalsaVerde.common.views import DeleteObjectView
from SalsaVerde.stock.models import (
    Container,
    ContainerType,
    Document,
    Ingredient,
    IngredientType,
    Product,
    ProductType,
    Supplier,
)
from SalsaVerde.stock.views import containers, documents, ingredients, products, suppliers

supplier_patterns = [
    path('', suppliers.supplier_list, name='suppliers'),
    path('add/', suppliers.supplier_add, name='suppliers-add'),
    path('<int:pk>/', suppliers.supplier_details, name='suppliers-details'),
    path('<int:pk>/edit/', suppliers.supplier_edit, name='suppliers-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Supplier), name='suppliers-delete'),
]

container_patterns = [
    path('', containers.containers_list, name='containers'),
    path('intake-goods/containers/', containers.intake_containers, name='intake-containers'),
    path('<int:pk>/', containers.containers_details, name='containers-details'),
    path('<int:pk>/edit/', containers.containers_edit, name='containers-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Container), name='containers-delete'),
    path('<int:pk>/status/', containers.change_container_status, name='container-status'),
    path('types/', containers.container_type_list, name='container-types'),
    path('types/add/', containers.container_type_add, name='container-types-add'),
    path('types/<int:pk>/delete/', DeleteObjectView.as_view(model=ContainerType), name='container-types-delete'),
    path('types/<int:pk>/', containers.container_type_details, name='container-types-details'),
    path('types/<int:pk>/edit/', containers.container_type_edit, name='container-types-edit'),
]

ingredient_patterns = [
    path('', ingredients.ingredient_list, name='ingredients'),
    path('<int:pk>/', ingredients.ingredient_details, name='ingredients-details'),
    path('<int:pk>/edit/', ingredients.ingredient_edit, name='ingredients-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Ingredient), name='ingredients-delete'),
    path('<int:pk>/status/', ingredients.change_ingredient_status, name='ingredient-status'),
    path('intake-goods/ingredients/', ingredients.intake_ingredients, name='intake-ingredients'),
    path('types/', ingredients.ingredient_type_list, name='ingredient-types'),
    path('types/add/', ingredients.ingredient_type_add, name='ingredient-types-add'),
    path('types/<int:pk>/', ingredients.ingredient_type_details, name='ingredient-types-details'),
    path('types/<int:pk>/edit/', ingredients.ingredient_type_edit, name='ingredient-types-edit'),
    path('types/<int:pk>/delete/', DeleteObjectView.as_view(model=IngredientType), name='ingredient-types-delete'),
]

document_patterns = [
    path('', documents.document_list, name='documents'),
    path('add/', documents.document_add, name='documents-add'),
    path('<int:pk>/', documents.document_details, name='documents-details'),
    path('<int:pk>/edit/', documents.document_edit, name='documents-edit'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Document), name='documents-delete'),
]

product_patterns = [
    path('', products.product_list, name='products'),
    path('add/', products.product_add, name='products-add'),
    path('<int:pk>/bottle/', products.product_bottle, name='products-bottle'),
    path('<int:pk>/', products.product_details, name='products-details'),
    path('<int:pk>/edit/', products.product_edit, name='products-edit'),
    path('<int:pk>/status/', products.change_product_status, name='product-status'),
    path('<int:pk>/delete/', DeleteObjectView.as_view(model=Product), name='products-delete'),
    path('<int:pk>/ingredients/add/', products.product_ingredient_add, name='product-ingredient-add'),
    path('<int:pk>/containers/add/', products.yield_container_add, name='yield-container-add'),
    path('types/', products.product_type_list, name='product-types'),
    path('types/add/', products.product_type_add, name='product-types-add'),
    path('types/<int:pk>/', products.product_type_details, name='product-types-details'),
    path('types/<int:pk>/edit/', products.product_type_edit, name='product-types-edit'),
    path('types/<int:pk>/delete/', DeleteObjectView.as_view(model=ProductType), name='product-types-delete'),
    path('types/size/<int:pk>/edit/', products.product_size_type_edit, name='product-type-sizes-edit'),
    path('types/size/<int:pk>/delete/', products.product_size_type_delete, name='product-type-sizes-delete'),
    path('types/<int:product_type>/size/add/', products.product_size_type_add, name='product-type-sizes-add'),
]

urlpatterns = [
    path('ingredients/', include(ingredient_patterns)),
    path('products/', include(product_patterns)),
    path('containers/', include(container_patterns)),
    path('suppliers/', include(supplier_patterns)),
    path('documents/', include(document_patterns)),
]
