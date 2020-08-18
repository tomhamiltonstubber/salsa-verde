from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.stock.factories.raw_materials import ContainerFactory, IngredientFactory
from SalsaVerde.stock.factories.supplier import SupplierFactory
from SalsaVerde.stock.models import IngredientType, Supplier
from SalsaVerde.stock.tests.test_common import AuthenticatedClient
from SalsaVerde.stock.views.base_views import display_dt


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
        self.assertNotContains(r, '<a href="mailto:')
        self.assertNotContains(r, '<a href="tel:')

    def test_supplier_list(self):
        sup = SupplierFactory(company=self.company, street='123 fake st')
        r = self.client.get(reverse('suppliers'))
        self.assertContains(r, reverse('suppliers-details', args=[sup.pk]))

    def test_delete_supplier(self):
        supplier = SupplierFactory(company=self.company)
        r = self.client.post(reverse('suppliers-delete', args=[supplier.pk]))
        self.assertRedirects(r, reverse('suppliers'))
        assert not Supplier.objects.exists()

    def test_display_ingredients(self):
        date = timezone.now()
        supplier = SupplierFactory(company=self.company)
        IngredientFactory(
            ingredient_type__company=self.company,
            batch_code='foo123',
            quantity=10,
            ingredient_type__name='blackberries',
            supplier=supplier,
            ingredient_type__unit=IngredientType.UNIT_LITRE,
            goods_intake__intake_date=date,
        )
        r = self.client.get(reverse('suppliers-details', args=[supplier.pk]))
        self.assertContains(r, 'Supplied Ingredients')
        self.assertContains(r, 'blackberries')
        self.assertContains(r, 'foo123')
        self.assertContains(r, '10.000 litre')
        self.assertContains(r, display_dt(date))

    def test_display_containers(self):
        supplier = SupplierFactory(company=self.company)
        container = ContainerFactory(container_type__name='abc', batch_code='foo123', quantity=10, supplier=supplier)
        r = self.client.get(reverse('suppliers-details', args=[supplier.pk]))
        self.assertContains(r, 'Supplied Containers')
        self.assertContains(r, 'abc')
        self.assertContains(r, 'foo123')
        self.assertContains(r, '10.000')
        self.assertContains(r, display_dt(container.goods_intake.date_created))
