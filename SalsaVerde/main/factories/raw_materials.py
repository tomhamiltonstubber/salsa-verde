import datetime

import factory
from django.utils import timezone

from SalsaVerde.main.factories.company import CompanyFactory
from SalsaVerde.main.factories.supplier import SupplierFactory
from SalsaVerde.main.factories.users import UserFactory
from SalsaVerde.main.models import IngredientType, ContainerType, ProductType, Ingredient, GoodsIntake, Container


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

    company = factory.SubFactory(CompanyFactory)
    sku_code = factory.Sequence(lambda n: 'SKU%d' % n)

    @factory.post_generation
    def dft_ingredient_types(self, create, ingredient_types, **kwargs):
        if ingredient_types:
            self.ingredient_types.add(*ingredient_types)
        else:
            self.ingredient_types.add(IngredientTypeFactory(company=self.company, name='ingred_type_1'))
            self.ingredient_types.add(IngredientTypeFactory(company=self.company, name='ingred_type_2'))


class GoodsIntakeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GoodsIntake

    intake_user = factory.SubFactory(UserFactory)
    date_created = factory.sequence(lambda n: timezone.now() - datetime.timedelta(hours=(n * 24)))
    intake_date = factory.sequence(lambda n: timezone.now() - datetime.timedelta(hours=(n * 24)))


class IngredientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ingredient

    ingredient_type = factory.SubFactory(
        IngredientTypeFactory,
        company=factory.SubFactory(CompanyFactory),
        name=factory.Sequence(lambda n: 'IngredType%d' % n)
    )
    batch_code = factory.Sequence(lambda n: 'ingred_%d' % n)
    supplier = factory.SubFactory(SupplierFactory, company=factory.SelfAttribute('..ingredient_type.company'))
    quantity = factory.Sequence(lambda n: n * 15)
    goods_intake = factory.SubFactory(
        GoodsIntakeFactory, intake_user__company=factory.SelfAttribute('...ingredient_type.company')
    )


class ContainerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Container

    container_type = factory.SubFactory(
        ContainerTypeFactory,
        company=factory.SubFactory(CompanyFactory),
        name=factory.Sequence(lambda n: 'ContainerType%d' % n)
    )
    batch_code = factory.Sequence(lambda n: 'container_%d' % n)
    supplier = factory.SubFactory(SupplierFactory, company=factory.SelfAttribute('..container_type.company'))
    quantity = factory.Sequence(lambda n: n * 15)
    goods_intake = factory.SubFactory(
        GoodsIntakeFactory, intake_user__company=factory.SelfAttribute('...container_type.company')
    )
