from datetime import datetime, timedelta

from django.conf import settings
from django.urls import reverse

from SalsaVerde.common.tests import SVTestCase
from SalsaVerde.stock.factories.raw_materials import IngredientFactory, IngredientTypeFactory
from SalsaVerde.stock.factories.supplier import SupplierFactory
from SalsaVerde.stock.factories.users import UserFactory
from SalsaVerde.stock.models import Ingredient, IngredientType
from SalsaVerde.stock.tests.test_common import AuthenticatedClient


class IngredientTypeTestCase(SVTestCase):
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

    def test_delete_ingredient_type(self):
        ingred_type = IngredientTypeFactory(company=self.company)
        r = self.client.post(reverse('ingredient-types-delete', args=[ingred_type.pk]))
        self.assertRedirects(r, reverse('ingredient-types'))
        assert not IngredientType.objects.exists()


class IngredientListTestCase(SVTestCase):
    def setUp(self):
        self.url = reverse('ingredients')
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.ingredient_type = IngredientTypeFactory(company=self.company, name='blackberries')

    def test_ingredient_list_empty(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'No Raw Ingredients found')

    def test_ingredient_list(self):
        IngredientFactory(batch_code='foo123', quantity=10, ingredient_type=self.ingredient_type)
        r = self.client.get(self.url)
        self.assertContains(r, 'blackberries')

    def test_ingredient_list_filter_finished(self):
        IngredientFactory(batch_code='Current123', quantity=10, ingredient_type=self.ingredient_type)
        IngredientFactory(batch_code='Finished123', quantity=10, ingredient_type=self.ingredient_type, finished=True)

        # By default, we shouldn't include finished ingredients
        r = self.client.get(self.url)
        self.assertContains(r, 'Current123')
        self.assertNotContains(r, 'Finished123')

        r = self.client.get(self.url + '?finished=finished')
        self.assertNotContains(r, 'Current123')
        self.assertContains(r, 'Finished123')

        r = self.client.get(self.url + '?finished=all')
        self.assertContains(r, 'Current123')
        self.assertContains(r, 'Finished123')

        r = self.client.get(self.url + '?finished=foo')
        self.assertNotContains(r, 'Current123')
        self.assertNotContains(r, 'Finished123')

    def test_ingredient_list_filter_ingredient_type(self):
        IngredientFactory(batch_code='Blackberries123', quantity=10, ingredient_type=self.ingredient_type)
        apples = IngredientTypeFactory(company=self.company, name='apples')
        IngredientFactory(batch_code='Apples123', quantity=10, ingredient_type=apples)

        r = self.client.get(self.url)
        self.assertContains(r, 'Blackberries123')
        self.assertContains(r, 'Apples123')

        r = self.client.get(self.url + f'?ingredient_type={apples.pk}')
        self.assertNotContains(r, 'Blackberries123')
        self.assertContains(r, 'Apples123')

        r = self.client.get(self.url + f'?ingredient_type={self.ingredient_type.pk}')
        self.assertContains(r, 'Blackberries123')
        self.assertNotContains(r, 'Apples123')

        r = self.client.get(self.url + '?ingredient_type=11111111')
        self.assertNotContains(r, 'Blackberries123')
        self.assertNotContains(r, 'Apples123')

    def test_ingredient_list_filter_supplier(self):
        supplier_1 = SupplierFactory(company=self.company)
        supplier_2 = SupplierFactory(company=self.company)
        IngredientFactory(
            batch_code='Blackberries123', quantity=10, supplier=supplier_1, ingredient_type=self.ingredient_type
        )
        IngredientFactory(
            batch_code='Apples123', quantity=10, supplier=supplier_2, ingredient_type=self.ingredient_type
        )

        r = self.client.get(self.url)
        self.assertContains(r, 'Blackberries123')
        self.assertContains(r, 'Apples123')

        r = self.client.get(self.url + f'?supplier={supplier_1.pk}')
        self.assertContains(r, 'Blackberries123')
        self.assertNotContains(r, 'Apples123')

        r = self.client.get(self.url + f'?supplier={supplier_2.pk}')
        self.assertNotContains(r, 'Blackberries123')
        self.assertContains(r, 'Apples123')

        r = self.client.get(self.url + '?supplier=11111111')
        self.assertNotContains(r, 'Blackberries123')
        self.assertNotContains(r, 'Apples123')

    def test_ingredient_list_filter_intake_user(self):
        user_2 = UserFactory(company=self.company)
        IngredientFactory(
            batch_code='Blackberry123',
            quantity=10,
            ingredient_type=self.ingredient_type,
            intake_user=self.user,
        )
        IngredientFactory(
            batch_code='Apple123',
            quantity=10,
            ingredient_type=self.ingredient_type,
            intake_user=user_2,
        )
        r = self.client.get(self.url)
        self.assertContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')

        r = self.client.get(self.url + f'?intake_user={self.user.pk}')
        self.assertContains(r, 'Blackberry123')
        self.assertNotContains(r, 'Apple123')

        r = self.client.get(self.url + f'?intake_user={user_2.pk}')
        self.assertNotContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')

        r = self.client.get(self.url + '?intake_user=11111111')
        self.assertNotContains(r, 'Blackberry123')
        self.assertNotContains(r, 'Apple123')

    def test_ingredient_list_filter_intake_date(self):
        intake_date_1 = datetime(2018, 2, 10)
        intake_date_2 = datetime(2018, 2, 20)
        IngredientFactory(
            batch_code='Blackberry123',
            quantity=10,
            ingredient_type=self.ingredient_type,
            intake_date=intake_date_1,
        )
        IngredientFactory(
            batch_code='Apple123',
            quantity=10,
            ingredient_type=self.ingredient_type,
            intake_date=intake_date_2,
        )
        r = self.client.get(self.url)
        self.assertContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')

        # First check up to the end of the last day
        r = self.client.get(self.url + f'?intake_date_to={intake_date_2}')
        self.assertContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')

        # Now check up to the start of the first day
        r = self.client.get(self.url + f'?intake_date_from={intake_date_1}')
        self.assertContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')

        # Now up to the 11th
        r = self.client.get(self.url + f'?intake_date_to={intake_date_1 + timedelta(days=1)}')
        self.assertContains(r, 'Blackberry123')
        self.assertNotContains(r, 'Apple123')

        # Now from the 11th
        r = self.client.get(self.url + f'?intake_date_from={intake_date_1 + timedelta(days=1)}')
        self.assertNotContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')

        # Now from the 11th to the 19th
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 + timedelta(days=1)}&intake_date_to={intake_date_2 - timedelta(days=1)}'
        )
        self.assertNotContains(r, 'Blackberry123')
        self.assertNotContains(r, 'Apple123')

        # Now from the 11th to the 21st
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 + timedelta(days=1)}&intake_date_to={intake_date_2 + timedelta(days=1)}'
        )
        self.assertNotContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')

        # Now from the 9th to the 19th
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 - timedelta(days=1)}&intake_date_to={intake_date_2 - timedelta(days=1)}'
        )
        self.assertContains(r, 'Blackberry123')
        self.assertNotContains(r, 'Apple123')

        # Now from the 9th to the 21st
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 - timedelta(days=1)}&intake_date_to={intake_date_2 + timedelta(days=1)}'
        )
        self.assertContains(r, 'Blackberry123')
        self.assertContains(r, 'Apple123')


class IngredientTestCase(SVTestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.add_url = reverse('ingredient-add')
        self.ingredient_type = IngredientTypeFactory(company=self.user.company, name='blackberries')
        self.supplier = SupplierFactory(name='good food', company=self.user.company)

    def test_intake_ingredients(self):
        r = self.client.get(self.add_url)
        self.assertContains(r, 'blackberries')
        self.assertContains(r, 'Intake Recipient')
        self.assertContains(r, self.supplier)
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'intake_notes': 'Foobar',
            'ingredient_type': self.ingredient_type.pk,
            'quantity': 10,
            'batch_code': '123abc',
            'supplier': self.supplier.pk,
        }
        r = self.client.post(self.add_url, data=data)
        ingred = Ingredient.objects.get()
        self.assertRedirects(r, reverse('ingredients-details', args=[ingred.pk]))

        assert ingred.ingredient_type == self.ingredient_type
        assert ingred.batch_code == '123abc'
        assert ingred.quantity == 10
        assert ingred.supplier == self.supplier
        assert ingred.intake_notes == 'Foobar'

        r = self.client.get(reverse('ingredients-details', args=[ingred.pk]))
        self.assertContains(r, 'Foobar')

    def test_intake_ingreds_unfilled_form(self):
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'supplier': self.supplier.pk,
        }
        r = self.client.post(self.add_url, data=data)
        self.assertContains(r, 'This field is required')

    def test_intake_ingreds_only_admins(self):
        non_admin = UserFactory(administrator=False, last_name='nonadmin', company=self.user.company)
        r = self.client.get(self.add_url)
        self.assertContains(r, self.user)
        self.assertNotContains(r, non_admin)

    def test_edit_ingredient(self):
        ingredient = Ingredient.objects.create(
            ingredient_type=self.ingredient_type,
            batch_code='foo123',
            quantity=10,
            supplier=self.supplier,
            intake_user=self.user,
        )
        r = self.client.get(reverse('ingredients-edit', args=[ingredient.pk]))
        self.assertContains(r, 'foo123')
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'intake_notes': 'Foobar',
            'ingredient_type': self.ingredient_type.pk,
            'quantity': 10,
            'batch_code': '123abc',
            'supplier': self.supplier.pk,
        }
        r = self.client.post(reverse('ingredients-edit', args=[ingredient.pk]), data=data)
        self.assertRedirects(r, reverse('ingredients-details', args=[ingredient.pk]))

        ingredient = Ingredient.objects.get()
        assert ingredient.ingredient_type == self.ingredient_type
        assert ingredient.batch_code == '123abc'
        assert ingredient.quantity == 10
        assert ingredient.supplier == self.supplier
        assert ingredient.intake_notes == 'Foobar'

    def test_delete_ingredient(self):
        ing = IngredientFactory(ingredient_type=self.ingredient_type, supplier=self.supplier)
        r = self.client.post(reverse('ingredients-delete', args=[ing.pk]))
        self.assertRedirects(r, reverse('ingredients'))
        assert not Ingredient.objects.exists()

    def test_ingredient_status(self):
        ing = IngredientFactory(ingredient_type=self.ingredient_type, supplier=None)
        assert not ing.finished
        r = self.client.post(reverse('ingredient-status', args=[ing.pk]), follow=True)
        self.assertRedirects(r, ing.get_absolute_url())
        assert Ingredient.objects.get().finished
        self.assertContains(r, 'Mark as In stock')
