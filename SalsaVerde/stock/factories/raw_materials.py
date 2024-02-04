import datetime

import factory
from django.utils import timezone

from SalsaVerde.stock.factories.company import CompanyFactory
from SalsaVerde.stock.factories.supplier import SupplierFactory
from SalsaVerde.stock.factories.users import UserFactory
from SalsaVerde.stock.models import (
    Container,
    ContainerType,
    Ingredient,
    IngredientType,
    ProductType,
    ProductTypeSize,
)


class IngredientTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IngredientType

    company = factory.SubFactory(CompanyFactory)

    name = factory.Sequence(lambda n: 'IngredType%d' % n)
    unit = IngredientType.UNIT_KILO


class ContainerTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContainerType

    company = factory.SubFactory(CompanyFactory)

    name = factory.Sequence(lambda n: 'ContainerType%d' % n)
    size = factory.Sequence(lambda n: n * 10)


class ProductTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductType
        skip_postgeneration_save = True

    company = factory.SubFactory(CompanyFactory)
    name = 'Blackberry and Thyme'
    code = 'BTT'

    @factory.post_generation
    def dft_ingredient_types(self, create, ingredient_types, **kwargs):
        if ingredient_types:
            self.ingredient_types.add(*ingredient_types)
        else:
            self.ingredient_types.add(IngredientTypeFactory(company=self.company, name='ingred_type_1'))
            self.ingredient_types.add(IngredientTypeFactory(company=self.company, name='ingred_type_2'))


class ProductTypeSizeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductTypeSize

    product_type = factory.SubFactory(ProductTypeFactory)
    sku_code = '987654'
    bar_code = '123foo456bar'
    size = 0.250


class IngredientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ingredient

    ingredient_type = factory.SubFactory(
        IngredientTypeFactory,
        company=factory.SubFactory(CompanyFactory),
        name=factory.Sequence(lambda n: 'IngredType%d' % n),
    )
    batch_code = factory.Sequence(lambda n: 'ingred_%d' % n)
    supplier = factory.SubFactory(SupplierFactory, company=factory.SelfAttribute('..ingredient_type.company'))
    quantity = factory.Sequence(lambda n: n * 15)


class ContainerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Container

    container_type = factory.SubFactory(
        ContainerTypeFactory,
        company=factory.SubFactory(CompanyFactory),
        name=factory.Sequence(lambda n: 'ContainerType%d' % n),
    )
    batch_code = factory.Sequence(lambda n: 'container_%d' % n)
    supplier = factory.SubFactory(SupplierFactory, company=factory.SelfAttribute('..container_type.company'))
    quantity = factory.Sequence(lambda n: n * 15)
