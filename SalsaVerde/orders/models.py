from django.contrib.postgres.fields import ArrayField
from django.db import models

from SalsaVerde.company.models import CompanyQueryset, Company


class Order(models.Model):
    objects = CompanyQueryset.as_manager()

    shipping_id = models.CharField(max_length=255)
    shopify_id = models.CharField(max_length=255)
    tracking_url = models.CharField(max_length=255)
    label_urls = ArrayField(models.CharField(max_length=255))
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    @property
    def order_info(self):
        return {'tracking_url': self.tracking_url, 'label_urls': self.label_urls}
