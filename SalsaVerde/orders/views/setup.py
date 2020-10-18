from SalsaVerde.common.views import AddModelView, DetailView, ListView, UpdateModelView
from SalsaVerde.orders.forms.setup import UpdatePackageTemplateForm
from SalsaVerde.orders.models import PackageTemplate


class PackageTemplateAdd(AddModelView):
    model = PackageTemplate
    form_class = UpdatePackageTemplateForm


package_temp_add = PackageTemplateAdd.as_view()


class PackageTemplateEdit(UpdateModelView):
    model = PackageTemplate
    form_class = UpdatePackageTemplateForm


package_temp_edit = PackageTemplateEdit.as_view()


class PackageTempDetails(DetailView):
    model = PackageTemplate
    display_items = [
        'name',
        'width',
        'length',
        'height',
    ]


package_temp_details = PackageTempDetails.as_view()


class PackageTempList(ListView):
    model = PackageTemplate
    display_items = [
        'name',
        'width',
        'length',
        'height',
    ]
    order_by = 'name'


package_temp_list = PackageTempList.as_view()
