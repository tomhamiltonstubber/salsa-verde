import decimal
from datetime import datetime as dt, datetime

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.main.factories.company import CompanyFactory
from SalsaVerde.main.factories.raw_materials import (ContainerFactory, IngredientTypeFactory, ContainerTypeFactory,
                                                     IngredientFactory, ProductTypeFactory, ProductTypeSizeFactory)
from SalsaVerde.main.factories.supplier import SupplierFactory
from SalsaVerde.main.factories.users import UserFactory
from SalsaVerde.main.models import User, Supplier, Document, IngredientType, ContainerType, Ingredient, GoodsIntake, \
    Container, YieldContainer, ProductIngredient, Product, ProductType, ProductTypeSize
from SalsaVerde.main.views.base_views import display_dt


def refresh(obj):
    return type(obj).objects.get(id=obj.id)


class AuthenticatedClient(Client):
    """
    Client an authenticated django.test.Client
    """

    def __init__(self):
        super().__init__()
        self.user = User.objects.create_user(first_name='Tom', last_name='Owner',
                                             email='owner@salsaverde.com', password='testing',
                                             company=CompanyFactory())
        logged_in = self.login(username=self.user.email, password='testing')
        if not logged_in:  # pragma: no cover
            raise RuntimeError('Not logged in')
        self.user = User.objects.get(pk=self.session['_auth_user_id'])


class UserTestCase(TestCase):
    user = None

    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user

    def test_login(self):
        user = User.objects.create(first_name='Brain', last_name='Johnson', email='testing@salsaverde.com',
                                   company=self.user.company)
        user.set_password('testing1')
        user.save()
        assert user.last_logged_in == dt(2018, 1, 1, tzinfo=timezone.utc)
        client = Client()
        r = client.get(reverse('suppliers'))
        self.assertRedirects(r, reverse('login'))
        r = client.post(reverse('login'), data={'username': 'testing@salsaverde.com', 'password': 'testing1'},
                        follow=True)
        self.assertRedirects(r, '/')
        self.assertNotContains(r, 'Login')
        assert refresh(user).last_logged_in.date() == timezone.now().date()

    def test_logout(self):
        r = self.client.post(reverse('logout'))
        self.assertRedirects(r, reverse('login'))
        r = self.client.get('/')
        self.assertRedirects(r, reverse('login'))

    def test_get_dashboard(self):
        r = self.client.get('/')
        assert r.status_code == 200

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
        assert refresh(self.user).last_name == 'Foobar'

    def test_add_user(self):
        add_url = reverse('users-add')
        r = self.client.get(add_url)
        self.assertContains(r, 'Create new User')
        r = self.client.post(add_url, data={'first_name': 'Bruce', 'last_name': 'Banner'})
        assert r.status_code == 200
        r = self.client.post(add_url, data={'first_name': 'Bruce', 'last_name': 'Banner', 'email': 'foo@example.com'})
        user = User.objects.get(email='foo@example.com')
        self.assertRedirects(r, reverse('users-details', args=[user.pk]))


class QSTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.wrong_company = CompanyFactory()

    def test_supplier_qs(self):
        supplier = SupplierFactory(company=self.company, name='correct')
        wrong_supplier = SupplierFactory(company=self.wrong_company, name='wrong')
        r = self.client.get(reverse('suppliers'))
        self.assertContains(r, supplier)
        self.assertNotContains(r, wrong_supplier)


class SupplierTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
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
        sup = SupplierFactory(company=self.company, street='123 fake st')
        r = self.client.get(reverse('suppliers-edit', args=[sup.pk]))
        self.assertContains(r, '123 fake st')
        self.data['name'] = 'red suppliers'
        r = self.client.post(reverse('suppliers-edit', args=[sup.pk]), data=self.data, follow=True)
        self.assertRedirects(r, reverse('suppliers-details', args=[sup.pk]))
        self.assertContains(r, 'red suppliers')

    def test_supplier_details(self):
        sup = SupplierFactory(company=self.company, street='123 fake st')
        r = self.client.get(reverse('suppliers-details', args=[sup.pk]))
        self.assertContains(r, f'<a href="mailto:{sup.email}">{sup.email}</a>')
        self.assertContains(r, f'<a href="tel:{sup.phone}">{sup.phone}</a>')
        sup = SupplierFactory(company=self.company, street='123 fake st', email=None, phone=None)
        r = self.client.get(reverse('suppliers-details', args=[sup.pk]))
        self.assertNotContains(r, f'<a href="mailto:')
        self.assertNotContains(r, f'<a href="tel:')

    def test_supplier_list(self):
        sup = SupplierFactory(company=self.company, street='123 fake st')
        r = self.client.get(reverse('suppliers'))
        self.assertContains(r, reverse('suppliers-details', args=[sup.pk]))

    def test_delete_supplier(self):
        # TODO
        pass

    def test_display_ingredients(self):
        date = timezone.now()
        supplier = SupplierFactory(company=self.company)
        IngredientFactory(ingredient_type__company=self.company, batch_code='foo123', quantity=10,
                          ingredient_type__name='blackberries', supplier=supplier,
                          ingredient_type__unit=IngredientType.UNIT_LITRE, goods_intake__intake_date=date)
        r = self.client.get(reverse('suppliers-details', args=[supplier.pk]))
        self.assertContains(r, 'Supplied Ingredients')
        self.assertContains(r, 'blackberries')
        self.assertContains(r, 'foo123')
        self.assertContains(r, '10.000 litre')
        self.assertContains(r, display_dt(date))

    def test_display_containers(self):
        date = timezone.now()
        supplier = SupplierFactory(company=self.company)
        ContainerFactory(container_type__name='abc', batch_code='foo123', quantity=10, supplier=supplier)
        r = self.client.get(reverse('suppliers-details', args=[supplier.pk]))
        self.assertContains(r, 'Supplied Containers')
        self.assertContains(r, 'abc')
        self.assertContains(r, 'foo123')
        self.assertContains(r, '10.000')
        self.assertContains(r, display_dt(date))


class DocumentTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.url = reverse('documents-add')

    def test_add_to_user(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'Salsa Form Type')
        other_user = UserFactory(company=self.company)
        r = self.client.post(self.url, data={'author': self.user.pk, 'focus': other_user.pk,
                                             'type': Document.FORM_VIS01})
        doc = Document.objects.get()
        self.assertRedirects(r, reverse('documents-details', args=[doc.pk]))
        r = self.client.get(reverse('users-details', args=[self.user.pk]))
        self.assertContains(r, 'VIS01 - Visitor Questionnaire')
        url = self.url + f'?focus={self.user.pk}'
        self.assertContains(r, url)
        r = self.client.get(url)
        self.assertContains(r, f'selected>{str(self.user)}</option>')

        r = self.client.get(reverse('users-details', args=[other_user.pk]))
        self.assertContains(r, 'VIS01 - Visitor Questionnaire')

    def test_add_to_supplier(self):
        sup = SupplierFactory(company=self.company)
        r = self.client.post(self.url, data={'author': self.user.pk, 'supplier': sup.pk, 'type': Document.FORM_VIS01})
        doc = Document.objects.get()
        self.assertRedirects(r, reverse('documents-details', args=[doc.pk]))
        r = self.client.get(reverse('suppliers-details', args=[sup.pk]))
        self.assertContains(r, 'VIS01 - Visitor Questionnaire')
        url = self.url + f'?supplier={sup.pk}'
        self.assertContains(r, url)
        r = self.client.get(url)
        self.assertContains(r, f'selected>{str(sup)}</option>')


class IngredientTypeTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.data = dict(name='ingredtype', unit=IngredientType.UNIT_LITRE)

    def test_add_ingredient_type(self):
        r = self.client.get(reverse('ingredient-types-add'))
        self.assertContains(r, 'Unit')
        r = self.client.post(reverse('ingredient-types-add'), data=self.data, follow=True)
        ct = IngredientType.objects.get()
        self.assertRedirects(r, reverse('ingredient-types-details', args=[ct.pk]))
        self.assertContains(r, 'ingredtype')

    def test_edit_ingredient_type(self):
        ingred_type = IngredientTypeFactory(company=self.company, name='ingredtype')
        r = self.client.get(reverse('ingredient-types-edit', args=[ingred_type.pk]))
        self.assertContains(r, 'ingredtype')
        self.data['name'] = 'ingredtype 2'
        r = self.client.post(reverse('ingredient-types-edit', args=[ingred_type.pk]), data=self.data, follow=True)
        self.assertRedirects(r, reverse('ingredient-types-details', args=[ingred_type.pk]))
        self.assertContains(r, 'ingredtype 2')

    def test_ingredient_type_list(self):
        ingred_type = IngredientTypeFactory(company=self.company)
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
        ct = ContainerType.objects.create(**data, company=self.user.company)
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
        ct = ContainerTypeFactory(company=self.user.company)
        r = self.client.get(reverse('container-types'))
        self.assertContains(r, reverse('container-types-details', args=[ct.pk]))


def _empty_formset(prefix):
    return {
        f'{prefix}-TOTAL_FORMS': 1,
        f'{prefix}-INITIAL_FORMS': 0,
        f'{prefix}-MIN_NUM_FORMS': 0,
        f'{prefix}-MAX_NUM_FORMS': 1000,
    }


class IngredientTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.intake_url = reverse('intake-ingredients')
        self.ingredient_type = IngredientTypeFactory(company=self.user.company, name='blackberries')
        self.supplier = SupplierFactory(name='good food', company=self.user.company)
        self.intake_management_data = _empty_formset('ingredients')

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
        assert goods_intake.intake_date.date() == datetime(2018, 2, 2).date()
        assert goods_intake.date_created.date() == timezone.now().date()
        assert goods_intake.intake_user == self.user
        doc = Document.objects.get()
        assert doc.type == Document.FORM_SUP01
        assert doc.author == self.user
        assert doc.goods_intake == goods_intake
        ingred = Ingredient.objects.get()
        assert ingred.ingredient_type == self.ingredient_type
        assert ingred.batch_code == '123abc'
        assert ingred.condition == 'Good'
        assert ingred.status == Ingredient.STATUS_ACCEPT
        assert ingred.goods_intake == goods_intake
        assert ingred.quantity == 10
        assert ingred.supplier == self.supplier

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
        assert refresh(ingred).batch_code == '123abc'


class ContainerTestCase(TestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.intake_url = reverse('intake-containers')
        self.container_type = ContainerTypeFactory(company=self.company, name='bottle', type=ContainerType.TYPE_BOTTLE)
        self.supplier = SupplierFactory(name='good bottle', company=self.company)
        self.intake_management_data = _empty_formset('containers')

    def test_intake_containers(self):
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
        assert goods_intake.intake_date.date() == datetime(2018, 2, 2).date()
        assert goods_intake.date_created.date() == timezone.now().date()
        assert goods_intake.intake_user == self.user
        doc = Document.objects.get()
        assert doc.type == Document.FORM_SUP02
        assert doc.author == self.user
        assert doc.goods_intake == goods_intake
        container = Container.objects.get()
        assert container.container_type == self.container_type
        assert container.batch_code == '123abc'
        assert container.condition == 'Good'
        assert container.status == Container.STATUS_ACCEPT
        assert container.goods_intake == goods_intake
        assert container.quantity == 10
        assert container.supplier == self.supplier

        r = self.client.get(reverse('containers-details', args=[container.pk]))
        self.assertContains(r, f'{reverse("documents-details", args=[doc.pk])}">SUP02')

    def test_edit_container(self):
        container = ContainerFactory(container_type=self.container_type, batch_code='foo123')
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
        assert refresh(container).batch_code == '123abc'


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
        ProductTypeSizeFactory(product_type=product_type, sku_code='aabbcc')
        r = self.client.get(reverse('product-types-edit', args=[product_type.id]))
        self.assertContains(r, 'aabbcc')
        data = {
            'name': product_type.name,
            'ingredient_types': [self.ingred_type_1.pk, self.ingred_type_2.pk, self.ingred_type_3.pk],
            'code': product_type.code,
            'product_type_sizes-0-sku-code': 'foo456',
            'product_type_sizes-0-bar-code': '9878765564',
            'product_type_sizes-0-size': '0.15',
            **self.management_data,
        }
        r = self.client.post(reverse('product-types-edit', args=[product_type.id]), data=data, follow=True)
        self.assertRedirects(r, reverse('product-types-details', args=[product_type.id]))
        self.assertContains(r, 'foo456')


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
        self.product_ingred_mngmnt = _empty_formset('productingredient_set')
        self.yield_containers_mngmnt = _empty_formset('yield_containers')
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
        assert YieldContainer.objects.count() == 2
        for yc in YieldContainer.objects.all():
            self.assertEquals(yc.product, product)
        pi = ProductIngredient.objects.get()
        assert product.product_type == self.product_type
        assert product.batch_code == 'foobar'
        assert product.date_of_bottling.date() == datetime(2018, 3, 3).date()
        assert product.date_of_infusion.date() == datetime(2018, 2, 2).date()
        assert product.yield_quantity == 25
        assert pi.product == product
        assert pi.ingredient == self.ingred
        assert pi.quantity == 10
