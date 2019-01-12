from django.test import TestCase
from django.urls import reverse

from SalsaVerde.main.factories.supplier import SupplierFactory
from SalsaVerde.main.factories.users import UserFactory
from SalsaVerde.main.models import Document
from SalsaVerde.main.tests.test_common import AuthenticatedClient


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
