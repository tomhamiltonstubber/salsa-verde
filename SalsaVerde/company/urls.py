from django.urls import path

from SalsaVerde.common.views import DeleteObjectView
from SalsaVerde.company.models import User
from SalsaVerde.company.views import setup, users

urlpatterns = [
    path('users/', users.user_list, name='users'),
    path('users/add/', users.user_add, name='users-add'),
    path('users/<int:pk>/', users.user_details, name='users-details'),
    path('users/<int:pk>/edit/', users.user_edit, name='users-edit'),
    path('users/<int:pk>/delete/', DeleteObjectView.as_view(model=User), name='users-delete'),
    path('setup/', setup.setup, name='setup'),
]
