from SalsaVerde.common.views import AddModelView, UpdateModelView
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
