from django.urls import reverse

from SalsaVerde.common.views import DetailView
from SalsaVerde.stock.models import Container, Product


class ContainerDetails(DetailView):
    model = Container
    display_items = [
        'obj_url|container_type',
        'quantity',
        'batch_code',
        'obj_url|supplier',
        'intake_date',
        'intake_user',
        'intake_quality_check',
        'finished',
        'intake_notes',
    ]

    def get_button_menu(self):
        btns = super().get_button_menu()
        if self.object.finished:
            label = 'Mark as In stock'
        else:
            label = 'Mark as Finished'
        btns[-1].append(
            {'name': label, 'url': reverse('container-status', kwargs={'pk': self.object.pk}), 'method': 'POST'}
        )
        return btns

    def extra_display_items(self):
        products = (
            Product.objects.request_qs(self.request)
            .filter(yield_containers__container=self.object)
            .select_related('product_type')
            .order_by('-date_of_bottling')
        )
        return [
            {
                'title': 'Products used in',
                'qs': products,
                'fields': ['product_type', 'batch_code', 'date_of_infusion', 'date_of_bottling', 'yield_quantity'],
            },
        ]


containers_details = ContainerDetails.as_view()
