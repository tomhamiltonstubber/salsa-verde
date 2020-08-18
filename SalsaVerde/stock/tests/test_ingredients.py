from datetime import datetime
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.stock.factories.raw_materials import IngredientFactory, IngredientTypeFactory
from SalsaVerde.stock.factories.supplier import SupplierFactory
from SalsaVerde.stock.models import Document, GoodsIntake, Ingredient, IngredientType
from SalsaVerde.stock.tests.test_common import AuthenticatedClient, _empty_formset, refresh


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

    def test_delete_ingredient_type(self):
        ingred_type = IngredientTypeFactory(company=self.company)
        r = self.client.post(reverse('ingredient-types-delete', args=[ingred_type.pk]))
        self.assertRedirects(r, reverse('ingredient-types'))
        assert not IngredientType.objects.exists()


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
        ingred = Ingredient.objects.create(
            ingredient_type=self.ingredient_type,
            batch_code='foo123',
            quantity=10,
            supplier=self.supplier,
            goods_intake=gi,
        )
        r = self.client.get(reverse('ingredients-edit', args=[ingred.pk]))
        self.assertContains(r, 'foo123')
        data = {
            'ingredient_type': self.ingredient_type.id,
            'supplier': self.supplier.id,
            'batch_code': '123abc',
            'quantity': 5,
            'condition': 'Good',
        }
        r = self.client.post(reverse('ingredients-edit', args=[ingred.pk]), data=data)
        self.assertRedirects(r, reverse('ingredients-details', args=[ingred.pk]))
        assert refresh(ingred).batch_code == '123abc'

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
