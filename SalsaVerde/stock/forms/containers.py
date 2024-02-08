import json

from django import forms

from SalsaVerde.stock.forms.base_forms import SVModelForm
from SalsaVerde.stock.models import Container, ContainerType, YieldContainer, Product


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


class ContainerForm(SVModelForm):
    intake_notes = forms.CharField(widget=forms.Textarea({'rows': 2, 'class': 'resize-vertical-only'}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        container_type_units_lu = dict(ContainerType.objects.request_qs(self.request).values_list('id', 'type'))
        self.fields['quantity'].widget.attrs.update(
            {
                'step': 0.01,
                'input-group-label-lu': 'cont_type_units',
                'input-group-text': 'Units',
                'cont_type_units': json.dumps(container_type_units_lu),
                'linked-input-id': 'id_container_type',
            },
        )

    class Meta:
        model = Container
        fields = [
            'supplier',
            'container_type',
            'quantity',
            'batch_code',
            'intake_quality_check',
            'intake_notes',
            'intake_user',
            'intake_date',
        ]
        layout = [
            ['intake_date', 'intake_user'],
            ['container_type', 'quantity'],
            ['supplier', 'batch_code'],
            [('intake_notes', 9), 'intake_quality_check'],
        ]


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
