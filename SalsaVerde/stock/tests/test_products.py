from datetime import datetime

from django.conf import settings
from django.urls import reverse

from SalsaVerde.common.tests import SVTestCase
from SalsaVerde.stock.factories.product import ProductFactory
from SalsaVerde.stock.factories.raw_materials import (
    ContainerFactory,
    IngredientFactory,
    IngredientTypeFactory,
    ProductTypeFactory,
)
from SalsaVerde.stock.models import (
    ContainerType,
    Product,
    ProductIngredient,
    ProductType,
    ProductTypeSize,
)
from SalsaVerde.stock.tests.test_common import AuthenticatedClient


class ProductTypeTestCase(SVTestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.ingred_type_1 = IngredientTypeFactory(company=self.company, name='blackberry')
        self.ingred_type_2 = IngredientTypeFactory(company=self.company, name='thyme')
        self.ingred_type_3 = IngredientTypeFactory(company=self.company, name='vinegar')
        self.add_url = reverse('product-types-add')

    def test_add_product_type(self):
        r = self.client.get(self.add_url)
        self.assertContains(r, 'blackberry')
        types = [self.ingred_type_1.pk, self.ingred_type_2.pk, self.ingred_type_3.pk]
        data = {
            'name': 'BBT',
            'ingredient_types': [self.ingred_type_1.pk, self.ingred_type_2.pk, self.ingred_type_3.pk],
            'code': 'BTT',
        }
        r = self.client.post(self.add_url, data=data, follow=True)
        pt = ProductType.objects.get()
        self.assertRedirects(r, reverse('product-types-details', args=[pt.pk]))
        assert pt.name == 'BBT'
        assert pt.code == 'BTT'

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

    def test_delete_ingredient_type(self):
        product_type = ProductTypeFactory(company=self.company)
        r = self.client.post(reverse('product-types-delete', args=[product_type.pk]))
        self.assertRedirects(r, reverse('product-types'))
        assert not ProductType.objects.exists()


class ProductTestCase(SVTestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company

        self.bottle = ContainerFactory(
            container_type__type=ContainerType.TYPE_BOTTLE, container_type__company=self.company
        )
        self.cap = ContainerFactory(container_type__type=ContainerType.TYPE_CAP, container_type__company=self.company)
        self.product_type = ProductTypeFactory(company=self.user.company)
        self.url = reverse('products-add')

    def test_add_product(self):
        r = self.client.get(self.url)
        ingred = IngredientFactory(batch_code='foo123', quantity=10, ingredient_type__company=self.company)
        self.assertContains(r, 'Batch Code')
        data = {
            'product_type': self.product_type.id,
            'batch_code': 'foobar',
            'date_of_infusion': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'ingredient_0': ingred.pk,
            'ingredient_quantity_0': 8,
        }
        r = self.client.post(self.url, data=data, follow=True)
        product = Product.objects.get()
        pi = ProductIngredient.objects.get()
        assert product.product_type == self.product_type
        assert product.batch_code == 'foobar'
        assert product.date_of_infusion.date() == datetime(2018, 2, 2).date()
        assert product.status == Product.STATUS_INFUSED
        assert pi.product == product
        assert pi.ingredient == ingred
        assert pi.quantity == 8

        self.assertRedirects(r, reverse('products-details', args=[product.pk]))
        self.assertContains(r, 'New product added')
        r = self.client.get(reverse('products-edit', args=[product.pk]))
        self.assertContains(r, pi.product.product_type.name)

        r = self.client.get(reverse('products'))
        self.assertContains(r, pi.product.product_type.name)

    def test_add_product_no_quantity(self):
        r = self.client.get(self.url)
        ingred = IngredientFactory(batch_code='foo123', quantity=10, ingredient_type__company=self.company)
        self.assertContains(r, 'Batch Code')
        data = {
            'product_type': self.product_type.id,
            'batch_code': 'foobar',
            'date_of_infusion': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'ingredient_0': ingred.pk,
            'ingredient_quantity_0': 8,
        }
        r = self.client.post(self.url, data=data, follow=True)
        product = Product.objects.get()
        pi = ProductIngredient.objects.get()
        assert product.product_type == self.product_type
        assert product.batch_code == 'foobar'
        assert product.date_of_infusion.date() == datetime(2018, 2, 2).date()
        assert product.status == Product.STATUS_INFUSED
        assert pi.product == product
        assert pi.ingredient == ingred
        assert pi.quantity == 8

        self.assertRedirects(r, reverse('products-details', args=[product.pk]))
        self.assertContains(r, 'New product added')
        r = self.client.get(reverse('products-edit', args=[product.pk]))
        self.assertContains(r, pi.product.product_type.name)

        r = self.client.get(reverse('products'))
        self.assertContains(r, pi.product.product_type.name)

    def test_add_product_no_ingred_quantities(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'Batch Code')
        data = {
            'product_type': self.product_type.id,
            'batch_code': 'foobar',
            'date_of_infusion': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'ingredient_quantity_0': 8,
        }
        r = self.client.post(self.url, data=data)
        self.assertContains(r, 'Ingredient is required')

        ingred = IngredientFactory(batch_code='foo123', quantity=10, ingredient_type__company=self.company)
        data = {
            'product_type': self.product_type.id,
            'batch_code': 'foobar',
            'date_of_infusion': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'ingredient_0': ingred.id,
        }
        r = self.client.post(self.url, data=data)
        self.assertContains(r, 'Quantity is required')

        data = {
            'product_type': self.product_type.id,
            'batch_code': 'foobar',
            'date_of_infusion': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
        }
        r = self.client.post(self.url, data=data)
        self.assertContains(r, 'Ingredient and quantities are required')

    def test_delete_product(self):
        product = ProductFactory(product_type=self.product_type)
        r = self.client.post(reverse('products-delete', args=[product.pk]))
        self.assertRedirects(r, reverse('products'))
        assert not Product.objects.exists()

    def test_add_product_ingredient(self):
        product = ProductFactory(product_type=self.product_type)
        url = reverse('product-ingredient-add', args=[product.pk])
        ingred = IngredientFactory(batch_code='foo123', quantity=10, ingredient_type__company=self.company)
        r = self.client.get(url)
        assert r.status_code == 200
        r = self.client.post(url, {'ingredient': ingred.pk, 'quantity': 12}, follow=True)
        self.assertRedirects(r, product.get_absolute_url())
        self.assertContains(r, 'foo123')

    def test_add_yield_container_no_cap(self):
        product = ProductFactory(product_type=self.product_type)
        url = reverse('yield-container-add', args=[product.pk])
        container = ContainerFactory(
            batch_code='foo456',
            quantity=10,
            container_type__company=self.company,
            container_type__type=ContainerType.TYPE_BOTTLE,
        )
        r = self.client.post(url, {'container': container.pk, 'quantity': 12})
        self.assertContains(r, 'You must select a cap')

    def test_add_yield_container(self):
        product = ProductFactory(product_type=self.product_type)
        url = reverse('yield-container-add', args=[product.pk])
        container = ContainerFactory(
            batch_code='foo456',
            quantity=10,
            container_type__company=self.company,
            container_type__type=ContainerType.TYPE_OTHER,
        )
        r = self.client.get(url)
        assert r.status_code == 200
        r = self.client.post(
            url,
            {'container': container.pk, 'quantity': 12, 'date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT)},
            follow=True,
        )
        self.assertRedirects(r, product.get_absolute_url())
        self.assertContains(r, 'foo456')

    def test_bottled_fields_viewable(self):
        product = ProductFactory(product_type=self.product_type, status=Product.STATUS_INFUSED)
        r = self.client.get(product.get_absolute_url())
        self.assertNotContains(r, 'Batch code applied')
        r = self.client.get(reverse('products-edit', args=[product.pk]))
        self.assertNotContains(r, 'Batch code applied')
        Product.objects.update(status=Product.STATUS_BOTTLED)
        r = self.client.get(product.get_absolute_url())
        self.assertContains(r, 'Batch code applied')
        r = self.client.get(reverse('products-edit', args=[product.pk]))
        self.assertContains(r, 'Batch code applied')


class ProductTypeSizeTestCase(SVTestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.product_type = ProductTypeFactory(company=self.client.user.company)

    def test_pst_form(self):
        r = self.client.post(
            reverse('product-type-sizes-add', args=[self.product_type.pk]),
            data={'name': 'PTS1', 'size': '100', 'sku_code': '123'},
            follow=True,
        )
        self.assertRedirects(r, self.product_type.get_absolute_url())
        pts = ProductTypeSize.objects.get()
        assert pts.size == 100
        assert pts.name == 'PTS1'
        self.assertContains(r, '123')
        assert list(ProductType.objects.get().product_type_sizes.all()) == [pts]

        r = self.client.get(reverse('product-type-sizes-edit', args=[pts.pk]))
        self.assertContains(r, 'PTS1')
        r = self.client.post(
            reverse('product-type-sizes-edit', args=[pts.pk]),
            data={'name': 'PTS2', 'size': '100', 'sku_code': '456'},
            follow=True,
        )
        self.assertRedirects(r, self.product_type.get_absolute_url())
        pts = ProductTypeSize.objects.get()
        assert pts.size == 100
        assert pts.name == 'PTS2'
        self.assertContains(r, '456')

    def test_delete_pst(self):
        pts = ProductTypeSize.objects.create(product_type=self.product_type, sku_code=123, name='pts1', size=100)
        r = self.client.get(reverse('product-type-sizes-edit', args=[pts.pk]))
        del_url = reverse('product-type-sizes-delete', args=[pts.pk])
        self.assertContains(r, del_url)
        r = self.client.get(del_url)
        assert r.status_code == 405
        r = self.client.post(del_url)
        self.assertRedirects(r, self.product_type.get_absolute_url())
