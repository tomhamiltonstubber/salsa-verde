from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from SalsaVerde.stock.models import (
    Company,
    Container,
    ContainerType,
    GoodsIntake,
    Ingredient,
    IngredientType,
    Product,
    ProductIngredient,
    ProductType,
    Supplier,
    User,
    YieldContainer,
)


class Command(BaseCommand):
    def handle(self, **kwargs):
        company = Company.objects.create(name='Test Company')

        user = User.objects.create_user(
            email='owner@salsaverde.com', first_name='Bruce', last_name='Banner', password='testing', company=company
        )
        supplier_1 = Supplier.objects.create(
            name='Green Food Suppliers',
            street='1 Fresh Fruit Avenue',
            town='Armagh',
            country='Northern Ireland',
            postcode='BT62 H90',
            email='green_food@example.com',
            main_contact='Beatrice',
            company=company,
        )
        supplier_2 = Supplier.objects.create(
            name='Modena Vinegar Suppliers',
            street='2 Pedro St',
            town='Modena',
            country='Italy',
            postcode='1h2b3n',
            email='modena_balsamic@example.com',
            main_contact='Mario',
            company=company,
        )
        bottle_type_200 = ContainerType.objects.create(
            name='200 ml bottle', size=0.2, type=ContainerType.TYPE_BOTTLE, company=company
        )
        bottle_type_100 = ContainerType.objects.create(
            name='100 ml bottle', size=0.1, type=ContainerType.TYPE_BOTTLE, company=company
        )
        cap_type = ContainerType.objects.create(name='Black Cap', type=ContainerType.TYPE_CAP, company=company)

        containers_intake = GoodsIntake.objects.create(
            intake_date=timezone.now(), date_created=timezone.now(), intake_user=user
        )
        bottle_200 = Container.objects.create(
            container_type=bottle_type_200,
            batch_code='123bot',
            goods_intake=containers_intake,
            quantity=1500,
        )
        bottle_100 = Container.objects.create(
            container_type=bottle_type_100, batch_code='456bot', goods_intake=containers_intake, quantity=1200
        )
        cap = Container.objects.create(
            container_type=cap_type, batch_code='789cap', goods_intake=containers_intake, quantity=2700
        )

        bb_type = IngredientType.objects.create(name='Blackberries', unit=IngredientType.UNIT_KILO, company=company)
        thyme_type = IngredientType.objects.create(name='Thyme', unit=IngredientType.UNIT_KILO, company=company)
        vinegar_type = IngredientType.objects.create(
            name='Black Balsamic', unit=IngredientType.UNIT_LITRE, company=company
        )

        three_days = timezone.now() - timedelta(days=3)
        ingreds_intake = GoodsIntake.objects.create(intake_date=three_days, date_created=three_days, intake_user=user)
        bb = Ingredient.objects.create(
            ingredient_type=bb_type, batch_code='bb123', supplier=supplier_1, quantity=20, goods_intake=ingreds_intake
        )
        thyme = Ingredient.objects.create(
            ingredient_type=thyme_type,
            batch_code='thy456',
            supplier=supplier_1,
            quantity=10,
            goods_intake=ingreds_intake,
        )
        vinegar = Ingredient.objects.create(
            ingredient_type=vinegar_type,
            batch_code='v789',
            supplier=supplier_2,
            quantity=95,
            goods_intake=ingreds_intake,
        )

        btt_type = ProductType.objects.create(name='Blackberry and Thyme', company=company)
        btt_type.ingredient_types.add(*(bb_type, thyme_type, vinegar_type))
        btt = Product.objects.create(
            product_type=btt_type,
            date_of_infusion=timezone.now() - timedelta(days=14),
            date_of_bottling=timezone.now(),
            date_of_best_before=timezone.now() + timedelta(days=365 * 2),
            yield_quantity=55,
            batch_code='BTT123ABC',
        )
        ProductIngredient.objects.create(product=btt, ingredient=bb, quantity=15)
        ProductIngredient.objects.create(product=btt, ingredient=thyme, quantity=0.5)
        ProductIngredient.objects.create(product=btt, ingredient=vinegar, quantity=52)
        YieldContainer.objects.create(product=btt, container=bottle_200, quantity=175)
        YieldContainer.objects.create(product=btt, container=bottle_100, quantity=200)
        YieldContainer.objects.create(product=btt, container=cap, quantity=375)
        print('User created with details:\n  owner@salsaverde.com\n  testing')
