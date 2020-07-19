import datetime
import factory
from django.utils import timezone

from SalsaVerde.main.factories.raw_materials import ContainerFactory, IngredientFactory, ProductTypeFactory
from SalsaVerde.main.models import Product, ProductIngredient, YieldContainer


class ProductIngredientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductIngredient

    ingredient = factory.SubFactory(IngredientFactory)
    quantity = 10


class YieldContainerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = YieldContainer

    container = factory.SubFactory(ContainerFactory)
    quantity = 10


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    product_type = factory.SubFactory(ProductTypeFactory)
    date_of_infusion = factory.sequence(lambda n: timezone.now() - datetime.timedelta(hours=(n * 48)))
    date_of_bottling = factory.sequence(lambda n: timezone.now() - datetime.timedelta(hours=(n * 24)))
    date_of_best_before = factory.sequence(lambda n: timezone.now() + datetime.timedelta(days=(n * 365 * 2)))
    yield_quantity = 40
    batch_code = 'abc123123'
    status = Product.STATUS_BOTTLED

    product_ingredient_1 = factory.RelatedFactory(
        ProductIngredientFactory,
        'product',
        ingredient__ingredient_type__company=factory.SelfAttribute('....product_type.company'),
    )
    product_ingredient_2 = factory.RelatedFactory(
        ProductIngredientFactory,
        'product',
        ingredient__ingredient_type__company=factory.SelfAttribute('....product_type.company'),
    )

    yield_container_1 = factory.RelatedFactory(
        YieldContainerFactory,
        'product',
        container__container_type__company=factory.SelfAttribute('....product_type.company'),
    )
    yield_container_2 = factory.RelatedFactory(
        YieldContainerFactory,
        'product',
        container__container_type__company=factory.SelfAttribute('....product_type.company'),
    )
