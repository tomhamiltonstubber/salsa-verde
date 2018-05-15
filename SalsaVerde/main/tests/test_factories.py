from django.test import TestCase

from SalsaVerde.main.factories import (CompanyFactory, SupplierFactory, UserFactory, IngredientTypeFactory,
                                       ProductTypeFactory, ContainerTypeFactory)
from SalsaVerde.main.factories.product import ProductFactory
from SalsaVerde.main.factories.raw_materials import IngredientFactory, ContainerFactory
from SalsaVerde.main.models import Company, Supplier, User, ProductType, Ingredient, Container


class FactoryTestCase(TestCase):
    def setUp(self):
        self.company = CompanyFactory()

    def test_company(self):
        for i in range(5):
            CompanyFactory()
        self.assertEqual(Company.objects.count(), 6)

    def test_supplier(self):
        for i in range(5):
            SupplierFactory(company=self.company)
        self.assertEqual(Supplier.objects.count(), 5)
        self.assertEqual(Supplier.objects.last().company, self.company)

    def test_user(self):
        for i in range(5):
            UserFactory(company=self.company)
        self.assertEqual(User.objects.count(), 5)

    def test_product_type(self):
        for i in range(5):
            ProductTypeFactory(company=self.company)
        self.assertEqual(ProductType.objects.count(), 5)

    def test_product_types(self):
        prod_type = ProductTypeFactory(company=self.company)
        self.assertEqual(prod_type.ingredient_types.count(), 2)
        self.assertTrue(all(i.company == self.company for i in prod_type.ingredient_types.all()))

        ingred_type = IngredientTypeFactory(company=self.company, name='foobar')
        new_prod_type = ProductTypeFactory(company=self.company, dft_ingredient_types=[ingred_type])
        self.assertEqual(new_prod_type.ingredient_types.get(), ingred_type)

    def test_ingredients(self):
        for i in range(5):
            IngredientFactory(ingredient_type__company=self.company)
        self.assertEqual(Ingredient.objects.count(), 5)
        self.assertEqual(Company.objects.count(), 1)

    def test_containers(self):
        ct = ContainerTypeFactory(company=self.company)
        for i in range(5):
            ContainerFactory(container_type=ct)
        self.assertEqual(Container.objects.count(), 5)
        self.assertEqual(Company.objects.count(), 1)

    def test_products(self):
        # Normal creation
        product = ProductFactory()
        # With 2 ingreds

        # With 2 containers
        ct = ContainerTypeFactory(company=self.company)
        for i in range(5):
            ContainerFactory(container_type=ct)
        self.assertEqual(Container.objects.count(), 5)
        self.assertEqual(Company.objects.count(), 1)
