from datetime import datetime as dt

from django.test import TestCase, Client

from SalsaVerde.main.models import *

"""
TODO:
  * Best before
  * Batch codes
  * Limit choices on product_ingredient formset
"""

def refresh(obj):
    return type(obj).objects.get(id=obj.id)


class AuthenticatedClient(Client):
    """
    Client an authenticated django.test.Client
    """

    def __init__(self):
        super().__init__()
        self.user = User.objects.create_user(first_name='Tom', last_name='Owner',
                                             email='owner@salsaverde.com', password='testing')
        logged_in = self.login(username=self.user.email, password='testing')
        if not logged_in:  # pragma: no cover
            raise RuntimeError('Not logged in')
        self.user = User.objects.get(pk=self.session['_auth_user_id'])


class MainTestCase(TestCase):
    user = None

    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user

    def test_login(self):
        user = User.objects.create(first_name='Brain', last_name='Johnson', email='testing@salsaverde.com')
        user.set_password('testing1')
        user.save()
        self.assertEqual(user.last_logged_in, dt(2018, 1, 1))
        client = Client()
        r = client.get(reverse('suppliers'))
        self.assertRedirects(r, reverse('login'))
        r = client.post(reverse('login'), data={'username': 'testing@salsaverde.com', 'password': 'testing1'},
                        follow=True)
        self.assertRedirects(r, '/')
        self.assertNotContains(r, 'Login')
        self.assertEqual(refresh(user).last_logged_in.date(), timezone.now().date())

    def test_get_dashboard(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_get_user_list(self):
        r = self.client.get(reverse('users'))
        self.assertContains(r, 'Owner')
        self.assertContains(r, reverse('users-details', args=[self.user.pk]))
        self.assertContains(r, 'First name')

    def test_get_user_details(self):
        r = self.client.get(reverse('users-details', args=[self.user.pk]))
        self.assertContains(r, 'Tom Owner')
        self.assertContains(r, reverse('users-edit', args=[self.user.pk]))

    def test_edit_user(self):
        edit_url = reverse('users-edit', args=[self.user.pk])
        r = self.client.get(edit_url)
        self.assertContains(r, 'Edit Tom Owner')
        r = self.client.post(edit_url, data={'last_name': 'Foobar', 'email': 'testing@salsaverde.com',
                                             'first_name': 'Tom'})
        self.assertRedirects(r, reverse('users-details', args=[self.user.pk]))
        self.assertEqual(refresh(self.user).last_name, 'Foobar')

    def test_add_user(self):
        add_url = reverse('users-add')
        r = self.client.get(add_url)
        self.assertContains(r, 'Create new User')
        r = self.client.post(add_url, data={'first_name': 'Bruce', 'last_name': 'Banner'})
        self.assertEqual(r.status_code, 200)
        r = self.client.post(add_url, data={'first_name': 'Bruce', 'last_name': 'Banner', 'email': 'foo@example.com'})
        user = User.objects.get(email='foo@example.com')
        self.assertRedirects(r, reverse('users-details', args=[user.pk]))


class SupplierTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.data = dict(
            name='green suppliers',
            street='123 fake st',
            postcode='abc123',
            town='foobar',
            country='uk',
            phone='123123123',
            email='g_s@example.com',
            main_contact='Graham',
        )

    def test_add_supplier(self):
        self.data.pop('name')
        r = self.client.get(reverse('suppliers-add'))
        self.assertContains(r, 'Street')
        r = self.client.post(reverse('suppliers-add'), data=self.data)
        assert r.status_code == 200
        assert Supplier.objects.count() == 0
        self.data['name'] = 'green suppliers'
        r = self.client.post(reverse('suppliers-add'), data=self.data, follow=True)
        sup = Supplier.objects.get()
        self.assertRedirects(r, reverse('suppliers-details', args=[sup.pk]))
        self.assertContains(r, '123 fake st, foobar')

    def test_edit_supplier(self):
        sup = Supplier.objects.create(**self.data)
        r = self.client.get(reverse('suppliers-edit', args=[sup.pk]))
        self.assertContains(r, '123 fake st')
        self.data['name'] = 'red suppliers'
        r = self.client.post(reverse('suppliers-edit', args=[sup.pk]), data=self.data, follow=True)
        self.assertRedirects(r, reverse('suppliers-details', args=[sup.pk]))
        self.assertContains(r, 'red suppliers')

    def test_supplier_details(self):
        sup = Supplier.objects.create(**self.data)
        r = self.client.get(reverse('suppliers-details', args=[sup.pk]))
        self.assertContains(r, f'<a href="mailto:{sup.email}">{sup.email}</a>')
        self.assertContains(r, f'<a href="tel:{sup.phone}">{sup.phone}</a>')
        sup = Supplier.objects.create(name='foo')
        r = self.client.get(reverse('suppliers-details', args=[sup.pk]))
        self.assertNotContains(r, f'<a href="mailto:')
        self.assertNotContains(r, f'<a href="tel:')

    def test_supplier_list(self):
        sup = Supplier.objects.create(**self.data)
        r = self.client.get(reverse('suppliers'))
        self.assertContains(r, reverse('suppliers-details', args=[sup.pk]))

    def test_delete_supplier(self):
        # TODO
        pass

    def test_display_ingredients(self):
        date = timezone.now()
        ingredient_type = IngredientType.objects.create(name='blackberries', unit=IngredientType.UNIT_LITRE)
        supplier = Supplier.objects.create(name='good food')
        gi = GoodsIntake.objects.create(intake_user=self.user, intake_date=date)
        ingred = Ingredient.objects.create(ingredient_type=ingredient_type, batch_code='foo123', quantity=10,
                                           supplier=supplier, goods_intake=gi)
        r = self.client.get(reverse('suppliers-details', args=[supplier.pk]))
        self.assertContains(r, 'Supplied Ingredients')
        self.assertContains(r, ingredient_type.name)
        self.assertContains(r, ingred.batch_code)
        self.assertContains(r, '10.000 litre')
        self.assertContains(r, display_dt(date))

    def test_display_containers(self):
        date = timezone.now()
        container_type = ContainerType.objects.create(name='200ml bottle', type=ContainerType.TYPE_BOTTLE)
        supplier = Supplier.objects.create(name='good containers')
        gi = GoodsIntake.objects.create(intake_user=self.user, intake_date=date)
        container = Container.objects.create(container_type=container_type, batch_code='foo345', quantity=40,
                                             supplier=supplier, goods_intake=gi)
        r = self.client.get(reverse('suppliers-details', args=[supplier.pk]))
        self.assertContains(r, 'Supplied Ingredients')
        self.assertContains(r, container_type.name)
        self.assertContains(r, container.batch_code)
        self.assertContains(r, '10.000')
        self.assertContains(r, display_dt(date))


class IngredientTypeTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.data = dict(name='ingredtype', unit=IngredientType.UNIT_LITRE)

    def test_add_ingredient_type(self):
        r = self.client.get(reverse('ingredient-types-add'))
        self.assertContains(r, 'Unit')
        r = self.client.post(reverse('ingredient-types-add'), data=self.data, follow=True)
        ct = IngredientType.objects.get()
        self.assertRedirects(r, reverse('ingredient-types-details', args=[ct.pk]))
        self.assertContains(r, 'ingredtype')

    def test_edit_ingredient_type(self):
        ct = IngredientType.objects.create(**self.data)
        r = self.client.get(reverse('ingredient-types-edit', args=[ct.pk]))
        self.assertContains(r, 'ingredtype')
        self.data['name'] = 'ingredtype 2'
        r = self.client.post(reverse('ingredient-types-edit', args=[ct.pk]), data=self.data, follow=True)
        self.assertRedirects(r, reverse('ingredient-types-details', args=[ct.pk]))
        self.assertContains(r, 'ingredtype 2')

    def test_ingredient_type_list(self):
        ingred_type = IngredientType.objects.create(**self.data)
        r = self.client.get(reverse('ingredient-types'))
        self.assertContains(r, reverse('ingredient-types-details', args=[ingred_type.pk]))


class ContainerTypeTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user

    def test_add_container_type(self):
        r = self.client.get(reverse('container-types-add'))
        self.assertContains(r, 'Size')
        data = dict(size=.200, name='bottle 1')
        r = self.client.post(reverse('container-types-add'), data=data)
        assert r.status_code == 200
        assert ContainerType.objects.count() == 0
        data['type'] = ContainerType.TYPE_BOTTLE
        r = self.client.post(reverse('container-types-add'), data=data, follow=True)
        ct = ContainerType.objects.get()
        self.assertRedirects(r, reverse('container-types-details', args=[ct.pk]))
        self.assertContains(r, 'bottle 1')

    def test_add_container_not_cap(self):
        r = self.client.get(reverse('container-types-add'))
        self.assertContains(r, 'Size')
        data = dict(name='bottle 1', type=ContainerType.TYPE_BOTTLE)
        r = self.client.post(reverse('container-types-add'), data=data)
        self.assertContains(r, 'You must enter a size')
        assert ContainerType.objects.count() == 0
        data = dict(name='bottle 1', type=ContainerType.TYPE_CAP)
        r = self.client.post(reverse('container-types-add'), data=data)
        ct = ContainerType.objects.get()
        self.assertRedirects(r, reverse('container-types-details', args=[ct.pk]))
        assert ContainerType.objects.count() == 1

    def test_edit_container_type(self):
        data = dict(name='bottle 1', type=ContainerType.TYPE_BOTTLE, size=.2)
        ct = ContainerType.objects.create(**data)
        r = self.client.get(reverse('container-types-edit', args=[ct.pk]))
        self.assertContains(r, 'bottle 1')
        data['name'] = 'bottle 2'
        r = self.client.post(reverse('container-types-edit', args=[ct.pk]), data=data, follow=True)
        self.assertRedirects(r, reverse('container-types-details', args=[ct.pk]))
        self.assertContains(r, 'bottle 2')

    def test_delete_container_type(self):
        # TODO
        pass

    def test_supplier_list(self):
        sup = ContainerType.objects.create(name='bottle 1', type=ContainerType.TYPE_BOTTLE, size=.2)
        r = self.client.get(reverse('container-types'))
        self.assertContains(r, reverse('container-types-details', args=[sup.pk]))


class IngredientTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.intake_url = reverse('intake-ingredients')
        self.ingredient_type = IngredientType.objects.create(name='blackberries', unit=IngredientType.UNIT_LITRE)
        self.supplier = Supplier.objects.create(name='good food')
        self.intake_management_data = {
            'ingredients-TOTAL_FORMS': 1,
            'ingredients-INITIAL_FORMS': 0,
            'ingredients-MIN_NUM_FORMS': 0,
            'ingredients-MAX_NUM_FORMS': 1000,
        }

    def test_intake_ingredients(self):
        r = self.client.get(self.intake_url)
        self.assertContains(r, 'blackberries')
        self.assertContains(r, 'Intake Recipient')
        self.assertContains(r, self.supplier)
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'ingredients-0-ingredient_type': self.ingredient_type.pk,
            'ingredients-0-quantity': 10,
            'ingredients-0-batch_code': '123abc',
            'ingredients-0-supplier': self.supplier.pk,
            'ingredients-0-condition': 'Good',
            'ingredients-0-status': Ingredient.STATUS_ACCEPT,
            **self.intake_management_data,
        }
        r = self.client.post(self.intake_url, data=data)
        self.assertRedirects(r, reverse('ingredients'))
        goods_intake = GoodsIntake.objects.get()
        self.assertEqual(goods_intake.intake_date.date(), datetime(2018, 2, 2).date())
        self.assertEqual(goods_intake.date_created.date(), timezone.now().date())
        self.assertEqual(goods_intake.intake_user, self.user)
        doc = Document.objects.get()
        self.assertEqual(doc.type, Document.FORM_SUP01)
        self.assertEqual(doc.author, self.user)
        self.assertEqual(doc.goods_intake, goods_intake)
        ingred = Ingredient.objects.get()
        self.assertEqual(ingred.ingredient_type, self.ingredient_type)
        self.assertEqual(ingred.batch_code, '123abc')
        self.assertEqual(ingred.condition, 'Good')
        self.assertEqual(ingred.status, Ingredient.STATUS_ACCEPT)
        self.assertEqual(ingred.goods_intake, goods_intake)
        self.assertEqual(ingred.quantity, 10)
        self.assertEqual(ingred.supplier, self.supplier)

        r = self.client.get(reverse('ingredients-details', args=[ingred.pk]))
        self.assertContains(r, f'{reverse("documents-details", args=[doc.pk])}">SUP01')

    def test_intake_ingreds_unfilled_form(self):
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'ingredients-0-supplier': self.supplier.pk,
            'ingredients-0-condition': 'Good',
            **self.intake_management_data,
        }
        r = self.client.post(self.intake_url, data=data)
        self.assertContains(r, 'This field is required')

    def test_edit_ingredient(self):
        gi = GoodsIntake.objects.create(intake_user=self.user)
        ingred = Ingredient.objects.create(ingredient_type=self.ingredient_type, batch_code='foo123',
                                           quantity=10, supplier=self.supplier, goods_intake=gi)
        r = self.client.get(reverse('ingredients-edit', args=[ingred.pk]))
        self.assertContains(r, 'foo123')
        data = {
            'ingredient_type': self.ingredient_type.id,
            'supplier': self.supplier.id,
            'batch_code': '123abc',
            'quantity': 5,
            'condition': 'Good',
            'status': Ingredient.STATUS_ACCEPT
        }
        r = self.client.post(reverse('ingredients-edit', args=[ingred.pk]), data=data)
        self.assertRedirects(r, reverse('ingredients-details', args=[ingred.pk]))
        self.assertEqual(refresh(ingred).batch_code, '123abc')


class ContainerTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.intake_url = reverse('intake-containers')
        self.container_type = ContainerType.objects.create(name='bottle', type=ContainerType.TYPE_BOTTLE)
        self.supplier = Supplier.objects.create(name='good bottle')
        self.intake_management_data = {
            'containers-TOTAL_FORMS': 1,
            'containers-INITIAL_FORMS': 0,
            'containers-MIN_NUM_FORMS': 0,
            'containers-MAX_NUM_FORMS': 1000,
        }

    def test_intake_ingredients(self):
        r = self.client.get(self.intake_url)
        self.assertContains(r, 'bottle')
        self.assertContains(r, 'Intake Recipient')
        self.assertContains(r, self.supplier)
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'containers-0-container_type': self.container_type.pk,
            'containers-0-quantity': 10,
            'containers-0-batch_code': '123abc',
            'containers-0-supplier': self.supplier.pk,
            'containers-0-condition': 'Good',
            'containers-0-status': Container.STATUS_ACCEPT,
            **self.intake_management_data,
        }
        r = self.client.post(self.intake_url, data=data)
        self.assertRedirects(r, reverse('containers'))
        goods_intake = GoodsIntake.objects.get()
        self.assertEqual(goods_intake.intake_date.date(), datetime(2018, 2, 2).date())
        self.assertEqual(goods_intake.date_created.date(), timezone.now().date())
        self.assertEqual(goods_intake.intake_user, self.user)
        doc = Document.objects.get()
        self.assertEqual(doc.type, Document.FORM_SUP02)
        self.assertEqual(doc.author, self.user)
        self.assertEqual(doc.goods_intake, goods_intake)
        container = Container.objects.get()
        self.assertEqual(container.container_type, self.container_type)
        self.assertEqual(container.batch_code, '123abc')
        self.assertEqual(container.condition, 'Good')
        self.assertEqual(container.status, Container.STATUS_ACCEPT)
        self.assertEqual(container.goods_intake, goods_intake)
        self.assertEqual(container.quantity, 10)
        self.assertEqual(container.supplier, self.supplier)

        r = self.client.get(reverse('containers-details', args=[container.pk]))
        self.assertContains(r, f'{reverse("documents-details", args=[doc.pk])}">SUP02')

    def test_edit_ingredient(self):
        gi = GoodsIntake.objects.create(intake_user=self.user)
        container = Container.objects.create(container_type=self.container_type, batch_code='foo123',
                                             quantity=10, supplier=self.supplier, goods_intake=gi)
        r = self.client.get(reverse('containers-edit', args=[container.pk]))
        self.assertContains(r, 'foo123')
        data = {
            'container_type': self.container_type.id,
            'supplier': self.supplier.id,
            'batch_code': '123abc',
            'quantity': 5,
            'condition': 'Good',
            'status': Container.STATUS_ACCEPT
        }
        r = self.client.post(reverse('containers-edit', args=[container.pk]), data=data)
        self.assertRedirects(r, reverse('containers-details', args=[container.pk]))
        self.assertEqual(refresh(container).batch_code, '123abc')


class ProductTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        date = timezone.now()
        self.user = self.client.user
        self.intake_url = reverse('intake-containers')
        self.container_type = ContainerType.objects.create(name='bottle', type=ContainerType.TYPE_BOTTLE)
        self.supplier = Supplier.objects.create(name='good bottle')
        ingredient_type = IngredientType.objects.create(name='blackberries', unit=IngredientType.UNIT_LITRE)
        gi = GoodsIntake.objects.create(intake_user=self.user, intake_date=date)
        self.ingred = Ingredient.objects.create(ingredient_type=ingredient_type, batch_code='foo123', quantity=10,
                                                supplier=self.supplier, goods_intake=gi)
        cap_type = ContainerType.objects.create(name='200ml bottle', type=ContainerType.TYPE_CAP)
        self.bottle = Container.objects.create(container_type=self.container_type, batch_code='foo345', quantity=40,
                                               supplier=self.supplier, goods_intake=gi)
        self.cap = Container.objects.create(container_type=cap_type, batch_code='foo345', quantity=40,
                                            supplier=self.supplier, goods_intake=gi)
        self.product_type = ProductType.objects.create(name='bbt')
        self.product_type.ingredient_types.add(ingredient_type)
        self.product_ingred_mngmnt = {
            'productingredient_set-TOTAL_FORMS': 1,
            'productingredient_set-INITIAL_FORMS': 0,
            'productingredient_set-MIN_NUM_FORMS': 0,
            'productingredient_set-MAX_NUM_FORMS': 1000,
        }
        self.yield_containers_mngmnt = {
            'yield_containers-TOTAL_FORMS': 1,
            'yield_containers-INITIAL_FORMS': 0,
            'yield_containers-MIN_NUM_FORMS': 0,
            'yield_containers-MAX_NUM_FORMS': 1000,
        }
        self.url = reverse('products-add')

    def test_add_product(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'Batch Code')
        data = {
            'productingredient_set-0-ingredient': self.ingred.pk,
            'productingredient_set-0-quantity': 10,
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
        r = self.client.post(self.url, data=data)
        product = Product.objects.get()
        self.assertRedirects(r, reverse('products-details', args=[product.pk]))
        self.assertEqual(YieldContainer.objects.count(), 2)
        for yc in YieldContainer.objects.all():
            self.assertEquals(yc.product, product)
        pi = ProductIngredient.objects.get()
        self.assertEqual(product.product_type, self.product_type)
        self.assertEqual(product.batch_code, 'foobar')
        self.assertEqual(product.date_of_bottling.date(), datetime(2018, 3, 3).date())
        self.assertEqual(product.date_of_infusion.date(), datetime(2018, 2, 2).date())
        self.assertEqual(product.yield_quantity, 25)
        self.assertEqual(pi.product, product)
        self.assertEqual(pi.ingredient, self.ingred)
        self.assertEqual(pi.quantity, 10)
