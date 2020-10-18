from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from SalsaVerde.company.models import Company, CompanyNameBaseModel, CompanyQueryset
from SalsaVerde.stock.models import Product


class Order(models.Model):
    DHL_CARRIER = 'dhl'
    EF_CARRIER = 'expressfreight'
    CARRIER_CHOICES = (
        (DHL_CARRIER, 'DHL'),
        (DHL_CARRIER, 'ExpressFreight'),
    )
    objects = CompanyQueryset.as_manager()

    shipping_id = models.CharField(max_length=255)
    shopify_id = models.CharField(max_length=255, null=True, blank=True)
    tracking_url = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    fulfilled = models.BooleanField(default=False)
    shipment_details = models.JSONField(blank=True, null=True)
    carrier = models.CharField(choices=CARRIER_CHOICES, max_length=20)

    def get_absolute_url(self):
        return reverse('order-details', kwargs={'pk': self.id})

    def __str__(self):
        return 'Order ' + self.shopify_id


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
