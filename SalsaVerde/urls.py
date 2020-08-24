from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import include, path

from SalsaVerde.common.views import dashboard, login

urlpatterns = [
    path('', dashboard, name='index'),
    path('login/', login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='base.jinja'), name='logout'),
    path('', include('SalsaVerde.company.urls')),
    path('orders/', include('SalsaVerde.orders.urls')),
    path('stock/', include('SalsaVerde.stock.urls')),
]


if settings.DEBUG:  # pragma: no cover
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
