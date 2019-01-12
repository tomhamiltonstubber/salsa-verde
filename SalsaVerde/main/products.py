from SalsaVerde.main.forms.base_forms import SVModelForm
from SalsaVerde.main.models import ProductTypeSize


class ProductTypeSizeForm(SVModelForm):
    class Meta:
        model = ProductTypeSize
        exclude = '',
