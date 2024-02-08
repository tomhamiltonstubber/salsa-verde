from django.urls import reverse

from SalsaVerde.common.tests import SVTestCase
from SalsaVerde.company.models import Company
from SalsaVerde.stock.factories.company import CompanyFactory
from SalsaVerde.stock.factories.users import UserFactory
from SalsaVerde.stock.tests.test_common import AuthenticatedClient


class CompanySetupTestCase(SVTestCase):
    def setUp(self):
        self.company = CompanyFactory(name='Burren')
        self.admin = UserFactory(company=self.company, last_name='FooCar')
        self.client = AuthenticatedClient(company=self.company)

    def test_details(self):
        assert not Company.objects.get(id=self.company.id).main_contact
        r = self.client.get(reverse('setup'))
        self.assertContains(r, 'Burren')
        self.assertContains(r, 'FooCar')
        assert Company.objects.get(id=self.company.id).main_contact == self.admin

    def test_edit_form(self):
        url = reverse('setup-company')
        r = self.client.get(url)
        self.assertContains(r, 'Burren')
        r = self.client.post(url, data={'website': 'https://foocar.com', 'name': 'Byebye'}, follow=True)
        self.assertRedirects(r, reverse('setup'))
        self.assertContains(r, 'Byebye')
        self.assertNotContains(r, 'Burren')

        c = Company.objects.get(id=self.company.id)
        assert c.name == 'Byebye'
        assert c.website == 'https://foocar.com'
