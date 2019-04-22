from django import forms

from SalsaVerde.main.forms.base_forms import SVModelForm
from SalsaVerde.main.models import ContainerType, Container, GoodsIntake, YieldContainer, Product


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
    container = forms.ModelChoiceField(Container.objects.none())
    cap = forms.ModelChoiceField(Container.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['container'].queryset = (
            Container.objects
            .request_qs(self.request)
            .filter(finished=False)
            .exclude(container_type__type=ContainerType.TYPE_CAP)
        )
        self.fields['cap'].queryset = (
            Container.objects
            .request_qs(self.request)
            .filter(finished=False, container_type__type=ContainerType.TYPE_CAP)
        )

    def clean(self):
        if (self.cleaned_data['container'].container_type.type == ContainerType.TYPE_BOTTLE and
                not self.cleaned_data.get('cap')):
            raise forms.ValidationError('You must select a cap if you are filling a bottle')
        return self.cleaned_data

    def save(self, commit=True):
        obj = super().save(commit)
        if commit:
            YieldContainer.objects.create(
                container=self.cleaned_data['cap'],
                quantity=self.cleaned_data['quantity'],
                product_id=obj.product.id
            )
        return obj

    class Meta:
        model = YieldContainer
        exclude = {'product'}


YieldContainersFormSet = forms.inlineformset_factory(Product, YieldContainer, YieldContainersForm, extra=1,
                                                     can_delete=False)
