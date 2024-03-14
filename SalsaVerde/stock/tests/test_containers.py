from datetime import datetime, timedelta

from django.conf import settings
from django.urls import reverse

from SalsaVerde.common.tests import SVTestCase
from SalsaVerde.stock.factories.raw_materials import ContainerFactory, ContainerTypeFactory
from SalsaVerde.stock.factories.supplier import SupplierFactory
from SalsaVerde.stock.factories.users import UserFactory
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
        }
        r = self.client.post(self.add_url, data=data)
        container = Container.objects.get()
        self.assertRedirects(r, reverse('containers-details', args=[container.pk]))

        assert container.container_type == self.container_type
        assert container.batch_code == '123abc'
        assert container.quantity == 10
        assert container.supplier == self.supplier
        assert container.intake_notes == 'Foobar'

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
        }
        r = self.client.post(reverse('containers-edit', args=[container.pk]), data=data)
        self.assertRedirects(r, reverse('containers-details', args=[container.pk]))

        container = Container.objects.get()
        assert container.container_type == self.container_type
        assert container.batch_code == '123abc'
        assert container.quantity == 10
        assert container.supplier == self.supplier
        assert container.intake_notes == 'Foobar'

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


class ContainerListTestCase(SVTestCase):
    def setUp(self):
        self.url = reverse('containers')
        self.client = AuthenticatedClient()
        self.user = self.client.user
        self.company = self.user.company
        self.container_type = ContainerTypeFactory(company=self.company, name='bottle')

    def test_container_list_empty(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'No Packaging found')

    def test_container_list(self):
        ContainerFactory(batch_code='foo123', quantity=10, container_type=self.container_type)
        r = self.client.get(self.url)
        self.assertContains(r, 'bottle')

    def test_container_list_filter_finished(self):
        ContainerFactory(batch_code='Current123', quantity=10, container_type=self.container_type)
        ContainerFactory(batch_code='Finished123', quantity=10, container_type=self.container_type, finished=True)

        # By default, we shouldn't include finished containers
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

    def test_container_list_filter_container_type(self):
        ContainerFactory(batch_code='Bottle123', quantity=10, container_type=self.container_type)
        box = ContainerTypeFactory(company=self.company, name='box')
        ContainerFactory(batch_code='Box123', quantity=10, container_type=box)

        r = self.client.get(self.url)
        self.assertContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        r = self.client.get(self.url + f'?container_type={box.pk}')
        self.assertNotContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        r = self.client.get(self.url + f'?container_type={self.container_type.pk}')
        self.assertContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

        r = self.client.get(self.url + '?container_type=11111111')
        self.assertNotContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

    def test_container_list_filter_supplier(self):
        supplier_1 = SupplierFactory(company=self.company)
        supplier_2 = SupplierFactory(company=self.company)
        ContainerFactory(batch_code='Bottle123', quantity=10, supplier=supplier_1, container_type=self.container_type)
        ContainerFactory(batch_code='Box123', quantity=10, supplier=supplier_2, container_type=self.container_type)

        r = self.client.get(self.url)
        self.assertContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        r = self.client.get(self.url + f'?supplier={supplier_1.pk}')
        self.assertContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

        r = self.client.get(self.url + f'?supplier={supplier_2.pk}')
        self.assertNotContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        r = self.client.get(self.url + '?supplier=11111111')
        self.assertNotContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

    def test_container_list_filter_intake_user(self):
        user_2 = UserFactory(company=self.company)
        ContainerFactory(
            batch_code='Bottle123',
            quantity=10,
            container_type=self.container_type,
            intake_user=self.user,
        )
        ContainerFactory(
            batch_code='Box123',
            quantity=10,
            container_type=self.container_type,
            intake_user=user_2,
        )
        r = self.client.get(self.url)
        self.assertContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        r = self.client.get(self.url + f'?intake_user={self.user.pk}')
        self.assertContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

        r = self.client.get(self.url + f'?intake_user={user_2.pk}')
        self.assertNotContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        r = self.client.get(self.url + '?intake_user=11111111')
        self.assertNotContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

    def test_container_list_filter_intake_date(self):
        intake_date_1 = datetime(2018, 2, 10)
        intake_date_2 = datetime(2018, 2, 20)
        ContainerFactory(
            batch_code='Bottle123',
            quantity=10,
            container_type=self.container_type,
            intake_date=intake_date_1,
        )
        ContainerFactory(
            batch_code='Box123',
            quantity=10,
            container_type=self.container_type,
            intake_date=intake_date_2,
        )
        r = self.client.get(self.url)
        self.assertContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        # First check up to the end of the last day
        r = self.client.get(self.url + f'?intake_date_to={intake_date_2}')
        self.assertContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        # Now check up to the start of the first day
        r = self.client.get(self.url + f'?intake_date_from={intake_date_1}')
        self.assertContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        # Now up to the 11th
        r = self.client.get(self.url + f'?intake_date_to={intake_date_1 + timedelta(days=1)}')
        self.assertContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

        # Now from the 11th
        r = self.client.get(self.url + f'?intake_date_from={intake_date_1 + timedelta(days=1)}')
        self.assertNotContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        # Now from the 11th to the 19th
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 + timedelta(days=1)}&intake_date_to={intake_date_2 - timedelta(days=1)}'
        )
        self.assertNotContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

        # Now from the 11th to the 21st
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 + timedelta(days=1)}&intake_date_to={intake_date_2 + timedelta(days=1)}'
        )
        self.assertNotContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')

        # Now from the 9th to the 19th
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 - timedelta(days=1)}&intake_date_to={intake_date_2 - timedelta(days=1)}'
        )
        self.assertContains(r, 'Bottle123')
        self.assertNotContains(r, 'Box123')

        # Now from the 9th to the 21st
        r = self.client.get(
            self.url
            + f'?intake_date_from={intake_date_1 - timedelta(days=1)}&intake_date_to={intake_date_2 + timedelta(days=1)}'
        )
        self.assertContains(r, 'Bottle123')
        self.assertContains(r, 'Box123')
