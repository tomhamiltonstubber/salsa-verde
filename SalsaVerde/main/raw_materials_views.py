from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from SalsaVerde.main.base_views import UpdateModelView, AddModelView, DetailView, ListView
from SalsaVerde.main.forms import (UpdateIngredientsForm, IngredientsFormSet, UpdateIngredientTypeForm,
                                   UpdateContainerForm, UpdateContainerTypeForm, ContainersFormSet, GoodsIntakeForm)
from SalsaVerde.main.models import Ingredient, Document, IngredientType, Container, ContainerType, GoodsIntake


class IngredientTypeList(ListView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]


ingredient_type_list = IngredientTypeList.as_view()


class IngredientTypeDetails(DetailView):
    model = IngredientType
    display_items = [
        'name',
        'unit',
    ]


ingredient_type_details = IngredientTypeDetails.as_view()


class IngredientTypeAdd(AddModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_add = IngredientTypeAdd.as_view()


class IngredientTypeEdit(UpdateModelView):
    model = IngredientType
    form_class = UpdateIngredientTypeForm


ingredient_type_edit = IngredientTypeEdit.as_view()


class IngredientList(ListView):
    model = Ingredient
    display_items = [
        'ingredient_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'supplier',
    ]

    def get_button_menu(self):
        return [
            ('Record ingredients intake', reverse('intake-ingredients')),
            ('Ingredient types', reverse('ingredient-types')),
        ]


ingredient_list = IngredientList.as_view()


class IngredientDetails(DetailView):
    model = Ingredient
    display_items = [
        'ingredient_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'condition',
        'supplier',
        'status',
        'quantity',
        ('Intake document', 'func|get_intake_document'),
    ]

    def get_intake_document(self, obj):
        if obj.intake_document:
            return mark_safe(f'<a href="{obj.intake_document.get_absolute_url()}">{obj.intake_document}</a>')
        return '–'


ingredient_details = IngredientDetails.as_view()


class IngredientEdit(UpdateModelView):
    model = Ingredient
    form_class = UpdateIngredientsForm


ingredient_edit = IngredientEdit.as_view()


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


class IntakeIngredients(AddGoodsIntake, AddModelView):
    document_type = Document.FORM_SUP01
    goods_model_formset = IngredientsFormSet
    success_url = 'ingredients'


intake_ingredients = IntakeIngredients.as_view()


class ContainerTypeList(ListView):
    model = ContainerType
    display_items = [
        'name',
        'size',
        'type',
    ]


container_type_list = ContainerTypeList.as_view()


class ContainerTypeDetails(DetailView):
    model = ContainerType
    display_items = [
        'name',
        'size',
        'type',
    ]


container_type_details = ContainerTypeDetails.as_view()


class ContainerTypeAdd(AddModelView):
    model = ContainerType
    form_class = UpdateContainerTypeForm


container_type_add = ContainerTypeAdd.as_view()


class ContainerTypeEdit(UpdateModelView):
    model = ContainerType
    form_class = UpdateContainerTypeForm


container_type_edit = ContainerTypeEdit.as_view()


class ContainerList(ListView):
    model = Container
    display_items = [
        'container_type',
        'batch_code',
    ]

    def get_button_menu(self):
        return [
            ('Record containers intake', reverse('intake-containers')),
            ('Container Types', reverse('container-types')),
        ]


containers_list = ContainerList.as_view()


class ContainerDetails(DetailView):
    model = Container
    display_items = [
        'container_type',
        'batch_code',
        ('Intake date', 'goods_intake__intake_date'),
        'condition',
        'supplier',
        'status',
        'quantity',
        ('Intake document', 'func|get_intake_document'),
    ]

    def get_intake_document(self, obj):
        if obj.intake_document:
            return mark_safe(f'<a href="{obj.intake_document.get_absolute_url()}">{obj.intake_document}</a>')
        return '–'

    def extra_display_items(self):
        return [
            {
                'title': 'Products used in',
                'qs': self.object.yield_containers.select_related('product'),
                'fields': [
                    ('Product', 'product__product_type__name'),
                    ('Batch code', 'product__batch_code'),
                    ('Date of infusion', 'product__date_of_infusion'),
                    ('Date of bottling', 'product__date_of_bottling'),
                    ('Best before', 'product__date_of_best_before'),
                    ('Quantity', 'product__yield_quantity'),
                ]
            },
        ]


containers_details = ContainerDetails.as_view()


class IntakeContainers(AddGoodsIntake, AddModelView):
    model = Container
    document_type = Document.FORM_SUP02
    goods_model_formset = ContainersFormSet
    success_url = 'containers'


intake_containers = IntakeContainers.as_view()


class ContainerEdit(UpdateModelView):
    model = Container
    form_class = UpdateContainerForm


containers_edit = ContainerEdit.as_view()
