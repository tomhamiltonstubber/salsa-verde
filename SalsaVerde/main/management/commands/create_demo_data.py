from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from SalsaVerde.main.models import User, ContainerType, Container, Supplier, IngredientType, Ingredient, ProductType, \
    Product, ProductIngredient, YieldContainer


class Command(BaseCommand):
    help = 'watch and build scss files'

    def handle(self, **kwargs):
        User.objects.create_user(email='owner@salsaverde.com', first_name='Bruce', last_name='Banner',
                                 password='testing')
        supplier_1 = Supplier.objects.create(
            name='Green Food Suppliers', street='1 Fresh Fruit Avenue', town='Armagh', country='Northern Ireland',
            postcode='BT62 H90', email='green_food@example.com', main_contact='Beatrice'
        )
        supplier_2 = Supplier.objects.create(
            name='Modena Vinegar Suppliers', street='2 Pedro St', town='Modena', country='Italy', postcode='1h2b3n',
            email='modena_balsamic@example.com', main_contact='Mario')
        bottle_type_200 = ContainerType.objects.create(name='200 ml bottle', size=0.2, type=ContainerType.TYPE_BOTTLE)
        bottle_type_100 = ContainerType.objects.create(name='100 ml bottle', size=0.1, type=ContainerType.TYPE_BOTTLE)
        cap_type = ContainerType.objects.create(name='Black Cap', type=ContainerType.TYPE_CAP)
        bottle_200 = Container.objects.create(container_type=bottle_type_200, batch_code='123bot')
        bottle_100 = Container.objects.create(container_type=bottle_type_100, batch_code='456bot')
        cap = Container.objects.create(container_type=cap_type, batch_code='789cap')
        bb_type = IngredientType.objects.create(name='Blackberries', unit=IngredientType.UNIT_KILO)
        thyme_type = IngredientType.objects.create(name='Thyme', unit=IngredientType.UNIT_KILO)
        vinegar_type = IngredientType.objects.create(name='Black Balsamic', unit=IngredientType.UNIT_LITRE)
        bb = Ingredient.objects.create(ingredient_type=bb_type, batch_code='bb123', supplier=supplier_1, quantity=20)
        thyme = Ingredient.objects.create(ingredient_type=thyme_type, batch_code='thy456', supplier=supplier_1,
                                          quantity=10)
        vinegar = Ingredient.objects.create(ingredient_type=vinegar_type, batch_code='v789', supplier=supplier_2,
                                            quantity=95)
        btt_type = ProductType.objects.create(name='Blackberry and Thyme')
        btt_type.ingredient_types.add(*(bb_type, thyme_type, vinegar_type))
        btt = Product.objects.create(product_type=btt_type,
                                     date_of_infusion=timezone.now() - timedelta(days=14),
                                     date_of_bottling=timezone.now(),
                                     date_of_best_before=timezone.now() + timedelta(days=365 * 2),
                                     yield_quantity=55,
                                     batch_code='BTT123ABC')
        ProductIngredient.objects.create(product=btt, ingredient=bb, quantity=15)
        ProductIngredient.objects.create(product=btt, ingredient=thyme, quantity=0.5)
        ProductIngredient.objects.create(product=btt, ingredient=vinegar, quantity=52)
        YieldContainer.objects.create(product=btt, container=bottle_200, quantity=175)
        YieldContainer.objects.create(product=btt, container=bottle_100, quantity=200)
        YieldContainer.objects.create(product=btt, container=cap, quantity=375)
        print('User created with details:\n  owner@salsaverde.com\n  testing')
