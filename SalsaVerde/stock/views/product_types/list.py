from SalsaVerde.common.views import ModelListView
from SalsaVerde.stock.models import ProductType


class ProductTypeList(ModelListView):
    model = ProductType
    display_items = [
        'name',
        'ingredient_types',
    ]
    order_by = 'name'


product_type_list = ProductTypeList.as_view()
