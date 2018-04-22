from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from SalsaVerde.main import views

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('admin/', admin.site.urls),

    path('users/', views.user_list, name='users'),
    path('users/add/', views.user_add, name='users-add'),
    path('users/<int:pk>/', views.user_details, name='users-details'),
    path('users/<int:pk>/edit/', views.user_edit, name='users-edit'),

    path('suppliers/', views.supplier_list, name='suppliers'),
    path('suppliers/add/', views.supplier_add, name='suppliers-add'),
    path('suppliers/<int:pk>/', views.supplier_details, name='suppliers-details'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='suppliers-edit'),

    path('ingredient-types/', views.ingredient_type_list, name='ingredient-types'),
    path('ingredient-types/add/', views.ingredient_type_add, name='ingredient-types-add'),
    path('ingredient-types/<int:pk>/', views.ingredient_type_details, name='ingredient-types-details'),
    path('ingredient-types/<int:pk>/edit/', views.ingredient_type_edit, name='ingredient-types-edit'),

    path('product-types/', views.product_type_list, name='product-types'),
    path('product-types/add/', views.product_type_add, name='product-types-add'),
    path('product-types/<int:pk>/', views.product_type_details, name='product-types-details'),
    path('product-types/<int:pk>/edit/', views.product_type_edit, name='product-types-edit'),

    path('container-types/', views.container_type_list, name='container-types'),
    path('container-types/add/', views.container_type_add, name='container-types-add'),
    path('container-types/<int:pk>/', views.container_type_details, name='container-types-details'),
    path('container-types/<int:pk>/edit/', views.container_type_edit, name='container-types-edit'),

    path('containers/', views.containers_list, name='containers'),
    path('containers/add/', views.containers_add, name='containers-add'),
    path('containers/<int:pk>/', views.containers_details, name='containers-details'),
    path('containers/<int:pk>/edit/', views.containers_edit, name='containers-edit'),

    path('ingredients/', views.ingredient_list, name='ingredients'),
    path('ingredients/<int:pk>/', views.ingredient_details, name='ingredients-details'),
    path('ingredients/<int:pk>/edit', views.ingredient_edit, name='ingredients-edit'),

    path('documents/', views.document_list, name='documents'),
    path('documents/add/', views.document_add, name='documents-add'),
    path('documents/<int:pk>/', views.document_details, name='documents-details'),
    path('documents/<int:pk>/edit/', views.document_edit, name='documents-edit'),


    path('products/', views.product_list, name='products'),
    path('products/add/', views.product_add, name='products-add'),
    path('products/<int:pk>/', views.product_details, name='products-details'),
    path('products/<int:pk>/edit/', views.product_edit, name='products-edit'),

    path('intake-goods/', views.intake_goods, name='intake-goods'),
]
