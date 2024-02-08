from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse

from SalsaVerde.common.views import SVFormsetForm, AddModelView, UpdateModelView, DeleteObjectView
from SalsaVerde.stock.forms.products import (
    UpdateProductTypeForm,
    ProductTypeSizesFormSet,
    UpdateProductTypeSizeForm,
    AddProductTypeSizeForm,
)
from SalsaVerde.stock.models import ProductType, ProductTypeSize


class ProductTypeAdd(SVFormsetForm, AddModelView):
    model = ProductType
    form_class = UpdateProductTypeForm
    template_name = 'formset_form.jinja'
    title = 'Add Product Type'
    formset_class = ProductTypeSizesFormSet
    cancel_url = reverse_lazy('product-types')

    def get_success_url(self):
        return self.object.get_absolute_url()


product_type_add = ProductTypeAdd.as_view()


class ProductTypeEdit(UpdateModelView):
    model = ProductType
    form_class = UpdateProductTypeForm

    def get_title(self):
        return f'Edit {self.object}'


product_type_edit = ProductTypeEdit.as_view()


class ProductTypeSizeEdit(UpdateModelView):
    model = ProductTypeSize
    form_class = UpdateProductTypeSizeForm
    title = 'Edit Product Size Type'
    template_name = 'edit_product_type_size.jinja'

    def get_cancel_url(self):
        return reverse('product-types-details', kwargs={'pk': self.object.product_type.pk})

    def form_valid(self, form):
        super().form_valid(form)
        return redirect('product-types-details', pk=self.object.product_type.pk)


product_size_type_edit = ProductTypeSizeEdit.as_view()


class ProductTypeSizeAdd(AddModelView):
    model = ProductTypeSize
    form_class = AddProductTypeSizeForm
    title = 'Add Product Size Type'

    def dispatch(self, request, *args, **kwargs):
        self.product_type = get_object_or_404(ProductType, pk=kwargs['product_type'])
        return super().dispatch(request, *args, **kwargs)

    def get_cancel_url(self):
        return reverse('product-types-details', kwargs={'pk': self.object.product_type.pk})

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.product_type = self.product_type
        obj.save()
        return redirect('product-types-details', pk=self.object.product_type.pk)


product_size_type_add = ProductTypeSizeAdd.as_view()


class ProductTypeSizeDelete(DeleteObjectView):
    model = ProductTypeSize

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model.objects.request_qs(request), pk=kwargs['pk'])
        pt_id = obj.product_type.id
        obj.delete()
        return redirect(reverse('product-types-details', kwargs={'pk': pt_id}))


product_size_type_delete = ProductTypeSizeDelete.as_view()
