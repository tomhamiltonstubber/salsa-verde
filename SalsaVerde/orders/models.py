from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from SalsaVerde.company.models import Company, CompanyNameBaseModel, CompanyQueryset, User
from SalsaVerde.stock.models import Product


class Order(models.Model):
    DHL_CARRIER = 'dhl'
    EF_CARRIER = 'expressfreight'
    CARRIER_CHOICES = (
        (DHL_CARRIER, 'DHL'),
        (DHL_CARRIER, 'ExpressFreight'),
    )
    STATUS_UNFULFILLED = 'unfulfilled'
    STATUS_FULFILLED = 'fulfilled'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_UNFULFILLED, 'Unfulfilled'),
        (STATUS_FULFILLED, 'Fulfilled'),
        (STATUS_CANCELLED, 'Cancelled/Deleted'),
    )

    objects = CompanyQueryset.as_manager()

    created = models.DateTimeField('Created', auto_now_add=True, db_index=True)
    shipping_id = models.CharField(max_length=255, null=True, blank=True)
    shopify_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    tracking_url = models.CharField(max_length=255, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, default=STATUS_UNFULFILLED, max_length=120)
    shipment_details = models.JSONField(blank=True, null=True)
    carrier = models.CharField(choices=CARRIER_CHOICES, max_length=20, null=True, blank=True)
    extra_data = models.JSONField(blank=True, null=True, default=dict)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    @classmethod
    def prefix(cls):
        return 'orders'

    def get_absolute_url(self):
        return reverse('order-details', kwargs={'pk': self.id})

    def __str__(self):
        return f'Order {self.shopify_id or self.id}'

    class Meta:
        ordering = ('-created',)


class PackageTemplate(CompanyNameBaseModel):
    width = models.DecimalField(verbose_name='Width (cm)', decimal_places=2, max_digits=6)
    length = models.DecimalField(verbose_name='Length (cm)', decimal_places=2, max_digits=6)
    height = models.DecimalField(verbose_name='Height (cm)', decimal_places=2, max_digits=6)
    weight = models.DecimalField(verbose_name='Weight (kg)', decimal_places=2, max_digits=6, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('package-temps-details', kwargs={'pk': self.pk})

    @classmethod
    def prefix(cls):
        return 'package-temps'

    class Meta:
        ordering = ('name',)
        verbose_name = 'Package Template'
        verbose_name_plural = 'Package Templates'


class ProductOrderQueryset(QuerySet):
    def request_qs(self, request):
        return self.filter(order__company=request.user.company)


class ProductOrder(models.Model):
    objects = ProductOrderQueryset.as_manager()
    quantity = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
