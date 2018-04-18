from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from SalsaVerde.main import views

urlpatterns = [
    url(r'^$', views.dashboard, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^users/$', views.user_list, name='users'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^admin/', admin.site.urls),
]
