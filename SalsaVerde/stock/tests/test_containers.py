from datetime import datetime

from django.conf import settings
from django.urls import reverse

from SalsaVerde.common.tests import SVTestCase
from SalsaVerde.stock.factories.raw_materials import ContainerFactory, ContainerTypeFactory
from SalsaVerde.stock.factories.supplier import SupplierFactory
from SalsaVerde.stock.models import Container, ContainerType
from SalsaVerde.stock.tests.test_common import AuthenticatedClient


class ContainerTypeTestCase(SVTestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user

    def test_add_container_type(self):
        r = self.client.get(reverse('container-types-add'))
        self.assertContains(r, 'Size')
        data = dict(size=0.200, name='bottle 1')
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
        data = dict(name='bottle 1', type=ContainerType.TYPE_BOTTLE, size=0.2)
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


class ContainerTestCase(SVTestCase):
    def setUp(self):
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.add_url = reverse('container-add')
        self.container_type = ContainerTypeFactory(company=self.company, name='bottle', type=ContainerType.TYPE_BOTTLE)
        self.supplier = SupplierFactory(name='good bottle', company=self.company)

    def test_intake_containers(self):
        r = self.client.get(self.add_url)
        self.assertContains(r, 'bottle')
        self.assertContains(r, 'Intake Recipient')
        self.assertContains(r, self.supplier)
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'intake_notes': 'Foobar',
            'container_type': self.container_type.pk,
            'quantity': 10,
            'batch_code': '123abc',
            'supplier': self.supplier.pk,
            'intake_quality_check': True,
        }
        r = self.client.post(self.add_url, data=data)
        self.assertRedirects(r, reverse('containers'))

        container = Container.objects.get()
        assert container.container_type == self.container_type
        assert container.batch_code == '123abc'
        assert container.quantity == 10
        assert container.supplier == self.supplier
        assert container.intake_notes == 'Foobar'
        assert container.intake_quality_check

        r = self.client.get(reverse('containers-details', args=[container.pk]))
        self.assertContains(r, 'Foobar')

    def test_edit_container(self):
        container = ContainerFactory(container_type=self.container_type, batch_code='foo123', intake_user=self.user)
        r = self.client.get(reverse('containers-edit', args=[container.pk]))
        self.assertContains(r, 'foo123')
        data = {
            'intake_date': datetime(2018, 2, 2).strftime(settings.DT_FORMAT),
            'intake_user': self.user.pk,
            'intake_notes': 'Foobar',
            'container_type': self.container_type.pk,
            'quantity': 10,
            'batch_code': '123abc',
            'supplier': self.supplier.pk,
            'intake_quality_check': True,
        }
        r = self.client.post(reverse('containers-edit', args=[container.pk]), data=data)
        self.assertRedirects(r, reverse('containers-details', args=[container.pk]))

        container = Container.objects.get()
        assert container.container_type == self.container_type
        assert container.batch_code == '123abc'
        assert container.quantity == 10
        assert container.supplier == self.supplier
        assert container.intake_notes == 'Foobar'
        assert container.intake_quality_check

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
