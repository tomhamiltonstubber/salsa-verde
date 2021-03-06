from django import forms

from SalsaVerde.stock.forms.base_forms import SVModelForm
from SalsaVerde.stock.models import Container, ContainerType, GoodsIntake, Product, YieldContainer


class UpdateContainerTypeForm(SVModelForm):
    class Meta:
        model = ContainerType
        exclude = {'company'}

    def clean_type(self):
        if self.cleaned_data['type'] != ContainerType.TYPE_CAP and not self.cleaned_data['size']:
            raise forms.ValidationError("You must enter a size if this isn't a cap")
        return self.cleaned_data['type']

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.request.user.company
        return super().save(commit)


class UpdateContainerForm(SVModelForm):
    title = 'Containers'

    class Meta:
        model = Container
        fields = ['container_type', 'quantity', 'batch_code', 'supplier']


ContainersFormSet = forms.inlineformset_factory(GoodsIntake, Container, UpdateContainerForm, extra=1, can_delete=False)


class YieldContainersForm(SVModelForm):
    title = 'Containers'
    container = forms.ModelChoiceField(
        queryset=(Container.objects.filter(finished=False).exclude(container_type__type=ContainerType.TYPE_CAP))
    )
    cap = forms.ModelChoiceField(
        queryset=(Container.objects.filter(finished=False, container_type__type=ContainerType.TYPE_CAP)), required=False
    )

    def clean(self):
        if self.cleaned_data[
            'container'
        ].container_type.type == ContainerType.TYPE_BOTTLE and not self.cleaned_data.get('cap'):
            raise forms.ValidationError('You must select a cap if you are filling a bottle')
        return self.cleaned_data

    def save(self, commit=True):
        obj = super().save(commit)
        if self.cleaned_data['cap']:
            YieldContainer.objects.create(
                container=self.cleaned_data['cap'], quantity=self.cleaned_data['quantity'], product_id=obj.product.id
            )
        return obj

    class Meta:
        model = YieldContainer
        fields = ['container', 'quantity']


YieldContainersFormSet = forms.inlineformset_factory(
    Product, YieldContainer, YieldContainersForm, extra=1, can_delete=False
)
