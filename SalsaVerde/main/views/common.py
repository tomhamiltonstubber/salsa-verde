from django.shortcuts import redirect
from django.urls import reverse

from .base_views import AddModelView
from SalsaVerde.main.forms import GoodsIntakeForm
from SalsaVerde.main.models import GoodsIntake, Document


class AddGoodsIntake(AddModelView):
    model = GoodsIntake
    form_class = GoodsIntakeForm
    template_name = 'intake_goods_form.jinja'
    title = 'Intake of goods'
    goods_model_formset = NotImplemented
    document_type = NotImplemented
    success_url = NotImplemented

    def form_valid(self, form):
        obj = form.save()
        self.goods_model_formset = self.goods_model_formset(self.request.POST)
        if self.goods_model_formset.is_valid():
            self.goods_model_formset.instance = obj
            self.goods_model_formset.save()
        else:
            return self.form_invalid(form)
        Document.objects.create(
            author=self.request.user,
            type=self.document_type,
            goods_intake=obj
        )
        return redirect(reverse(self.success_url))

    def get_context_data(self, **kwargs):
        if self.request.POST:
            formset = self.goods_model_formset
        else:
            formset = self.goods_model_formset()
        return super().get_context_data(formsets=formset, **kwargs)
