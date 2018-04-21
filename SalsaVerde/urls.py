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

    path('ingredients/', views.ingredient_list, name='ingredients'),
    path('ingredients/<int:pk>/', views.ingredient_details, name='ingredients-details'),

    path('intake-goods/', views.intake_goods, name='intake-goods'),
]
