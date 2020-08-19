from django.urls import path

from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.orders.views.dhl import dhl_label_create
from SalsaVerde.orders.views.express_freight import ef_label_create
from SalsaVerde.orders.views.setup import package_temp_add, package_temp_edit
from SalsaVerde.orders.views.shopify import shopify_orders
from SalsaVerde.stock.views.base_views import DeleteObjectView

urlpatterns = [
    path('', shopify_orders, name='shopify-orders'),
    path('setup/package-temp/add/', package_temp_add, name='package-temp-add'),
    path('setup/package-temp/<int:pk>/edit/', package_temp_edit, name='package-temp-edit'),
    path(
        'setup/package-temp/<int:pk>/delete/',
        DeleteObjectView.as_view(model=PackageTemplate),
        name='package-temp-delete',
    ),
    path('fulfill/express/', ef_label_create, name='fulfill-order-ef'),
    path('fulfill/dhl/', dhl_label_create, name='fulfill-order-dhl'),
]
