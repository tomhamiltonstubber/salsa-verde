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
]
