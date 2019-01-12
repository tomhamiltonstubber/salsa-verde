import decimal
from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from SalsaVerde.main.factories.product import ProductFactory
from SalsaVerde.main.factories.raw_materials import IngredientTypeFactory, ProductTypeFactory, IngredientFactory, \
    ContainerFactory
from SalsaVerde.main.models import ProductType, ProductTypeSize, ContainerType, Product, YieldContainer, \
    ProductIngredient
from SalsaVerde.main.tests.test_common import _empty_formset, AuthenticatedClient


class ProductTypeTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.ingred_type_1 = IngredientTypeFactory(company=self.company, name='blackberry')
        self.ingred_type_2 = IngredientTypeFactory(company=self.company, name='thyme')
        self.ingred_type_3 = IngredientTypeFactory(company=self.company, name='vinegar')
        self.add_url = reverse('product-types-add')
        self.management_data = _empty_formset('product_type_sizes')

    def test_add_product_type(self):
        r = self.client.get(self.add_url)
        self.assertContains(r, 'blackberry')
        types = [self.ingred_type_1.pk, self.ingred_type_2.pk, self.ingred_type_3.pk]
        data = {
            'name': 'BBT',
            'ingredient_types': [self.ingred_type_1.pk, self.ingred_type_2.pk, self.ingred_type_3.pk],
            'code': 'BTT',
            'product_type_sizes-0-sku_code': 'foo456',
            'product_type_sizes-0-bar_code': '9878765564',
            'product_type_sizes-0-size': '0.15',
            **self.management_data,
        }
        r = self.client.post(self.add_url, data=data, follow=True)
        pt = ProductType.objects.get()
        self.assertRedirects(r, reverse('product-types-details', args=[pt.pk]))
        assert pt.name == 'BBT'
        assert pt.code == 'BTT'
        pts = ProductTypeSize.objects.get()
        assert pts.sku_code == 'foo456'
        assert pts.size == round(decimal.Decimal(0.15), 2)
        assert pts.bar_code == '9878765564'
        assert list(pt.ingredient_types.values_list('pk', flat=True)) == types
        self.assertContains(r, 'blackberry, thyme, vinegar')
        r = self.client.get(reverse('product-types'))
        self.assertContains(r, 'blackberry, thyme, vinegar')

    def test_update_product_type(self):
        product_type = ProductTypeFactory(company=self.company)
        r = self.client.get(reverse('product-types-edit', args=[product_type.id]))
        data = {
            'name': product_type.name,
            'ingredient_types': [self.ingred_type_1.pk, self.ingred_type_2.pk, self.ingred_type_3.pk],
            'code': product_type.code,
        }
        self.assertNotContains(r, 'product_type_sizes')
        r = self.client.post(reverse('product-types-edit', args=[product_type.id]), data=data, follow=True)
        self.assertRedirects(r, reverse('product-types-details', args=[product_type.id]))
        self.assertContains(r, 'blackberry')


class ProductTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.intake_url = reverse('intake-containers')

        self.ingred = IngredientFactory(batch_code='foo123', quantity=10, ingredient_type__company=self.company)
        self.bottle = ContainerFactory(container_type__type=ContainerType.TYPE_BOTTLE,
                                       container_type__company=self.company)
        self.cap = ContainerFactory(container_type__type=ContainerType.TYPE_CAP, container_type__company=self.company)
        self.product_type = ProductTypeFactory(company=self.user.company)
        self.product_ingred_mngmnt = _empty_formset('product_ingredients')
        self.yield_containers_mngmnt = _empty_formset('yield_containers')
        self.url = reverse('products-add')

    def test_add_product(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'Batch Code')
        data = {
            'product_ingredients-0-ingredient': self.ingred.pk,
            'product_ingredients-0-quantity': 10,
            'yield_containers-0-container': self.bottle.pk,
            'yield_containers-0-cap': self.cap.pk,
            'yield_containers-0-quantity': 15,
            'product_type': self.product_type.pk,
            'date_of_bottling': datetime(2018, 3, 3).strftime(settings.DT_FORMAT),
            'date_of_infusion': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'batch_code': 'foobar',
            'yield_quantity': 25,
            **self.product_ingred_mngmnt,
            **self.yield_containers_mngmnt,
        }
        r = self.client.post(self.url, data=data, follow=True)
        product = Product.objects.get()
        assert YieldContainer.objects.count() == 2
        for yc in YieldContainer.objects.all():
            assert yc.product == product
        pi = ProductIngredient.objects.get()
        assert product.product_type == self.product_type
        assert product.batch_code == 'foobar'
        assert product.date_of_bottling.date() == datetime(2018, 3, 3).date()
        assert product.date_of_infusion.date() == datetime(2018, 2, 2).date()
        assert product.yield_quantity == 25
        assert pi.product == product
        assert pi.ingredient == self.ingred
        assert pi.quantity == 10

        self.assertRedirects(r, reverse('products-details', args=[product.pk]))
        self.assertContains(r, self.cap.name)
        self.assertContains(r, self.bottle.name)
        self.assertContains(r, self.ingred.name)

        r = self.client.get(reverse('products-edit', args=[product.pk]))
        self.assertContains(r, pi.product.product_type.name)

        r = self.client.get(reverse('products'))
        self.assertContains(r, pi.product.product_type.name)
