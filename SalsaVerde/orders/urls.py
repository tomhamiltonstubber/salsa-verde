from django.urls import path

from SalsaVerde.common.views import DeleteObjectView
from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.orders.views import shopify
from SalsaVerde.orders.views.common import order_details, orders_list, update_packed_product
from SalsaVerde.orders.views.dhl import dhl_order_create
from SalsaVerde.orders.views.express_freight import ef_order_create
from SalsaVerde.orders.views.setup import package_temp_add, package_temp_details, package_temp_edit, package_temp_list

urlpatterns = [
    path('', orders_list, name='orders-list'),
    path('<int:pk>/', order_details, name='order-details'),
    path('<int:pk>/update-product', update_packed_product, name='order-packed-product'),
    path('setup/package-temp/', package_temp_list, name='package-temps'),
    path('setup/package-temp/add/', package_temp_add, name='package-temps-add'),
    path('setup/package-temp/<int:pk>/', package_temp_details, name='package-temps-details'),
    path('setup/package-temp/<int:pk>/edit/', package_temp_edit, name='package-temps-edit'),
    path(
        'setup/package-temp/<int:pk>/delete/',
        DeleteObjectView.as_view(model=PackageTemplate),
        name='package-temps-delete',
    ),
    path('<int:pk>/fulfill/express/', ef_order_create, name='fulfill-order-ef'),
    path('<int:pk>/fulfill/dhl/', dhl_order_create, name='fulfill-order-dhl'),
    path('shopify/callback/', shopify.callback, name='shopify-callback'),
]
