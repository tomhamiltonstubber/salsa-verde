from django.urls import path

from SalsaVerde.common.views import DeleteObjectView
from SalsaVerde.orders.models import PackageTemplate
from SalsaVerde.orders.views.common import order_details, orders_list, shopify_order_details, update_packed_product
from SalsaVerde.orders.views.dhl import dhl_order_create
from SalsaVerde.orders.views.express_freight import ef_order_create
from SalsaVerde.orders.views.setup import package_temp_add, package_temp_edit

urlpatterns = [
    path('', orders_list, name='orders-list'),
    path('<int:pk>/', order_details, name='order-details'),
    path('<int:pk>/update-product', update_packed_product, name='order-packed-product'),
    path('shopify/<int:id>/', shopify_order_details, name='order-details-shopify'),
    path('setup/package-temp/add/', package_temp_add, name='package-temp-add'),
    path('setup/package-temp/<int:pk>/edit/', package_temp_edit, name='package-temp-edit'),
    path(
        'setup/package-temp/<int:pk>/delete/',
        DeleteObjectView.as_view(model=PackageTemplate),
        name='package-temp-delete',
    ),
    path('fulfill/express/', ef_order_create, name='fulfill-order-ef'),
    path('fulfill/dhl/', dhl_order_create, name='fulfill-order-dhl'),
]
