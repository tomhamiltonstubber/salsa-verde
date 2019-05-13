from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.main.factories.raw_materials import ContainerTypeFactory, ContainerFactory
from SalsaVerde.main.factories.supplier import SupplierFactory
from SalsaVerde.main.models import ContainerType, Container, GoodsIntake, Document
from SalsaVerde.main.tests.test_common import _empty_formset, AuthenticatedClient, refresh


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
        con_type = ContainerTypeFactory(company=self.user.company)
        r = self.client.post(reverse('container-types-delete', args=[con_type.pk]))
        self.assertRedirects(r, reverse('container-types'))
        assert not ContainerType.objects.exists()

    def test_supplier_list(self):
        ct = ContainerTypeFactory(company=self.user.company)
        r = self.client.get(reverse('container-types'))
        self.assertContains(r, reverse('container-types-details', args=[ct.pk]))


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
        }
        r = self.client.post(reverse('containers-edit', args=[container.pk]), data=data)
        self.assertRedirects(r, reverse('containers-details', args=[container.pk]))
        assert refresh(container).batch_code == '123abc'

    def test_delete_container(self):
        con = ContainerFactory(container_type=self.container_type)
        r = self.client.post(reverse('containers-delete', args=[con.pk]))
        self.assertRedirects(r, reverse('containers'))
        assert not Container.objects.exists()

    def test_container_status(self):
        con = ContainerFactory(container_type=self.container_type, supplier=None)
        assert not con.finished
        r = self.client.post(reverse('container-status', args=[con.pk]), follow=True)
        self.assertRedirects(r, con.get_absolute_url())
        assert Container.objects.get().finished
        self.assertContains(r, 'Mark as In stock')
