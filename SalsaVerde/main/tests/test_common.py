from django.test import TestCase, Client
from django.urls import reverse

from SalsaVerde.main.factories.company import CompanyFactory
from SalsaVerde.main.factories.raw_materials import ProductTypeFactory, IngredientTypeFactory, ContainerTypeFactory
from SalsaVerde.main.factories.supplier import SupplierFactory
from SalsaVerde.main.models import User


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


def _empty_formset(prefix):
    return {
        f'{prefix}-TOTAL_FORMS': 1,
        f'{prefix}-INITIAL_FORMS': 0,
        f'{prefix}-MIN_NUM_FORMS': 0,
        f'{prefix}-MAX_NUM_FORMS': 1000,
    }


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


def refresh(obj):
    return type(obj).objects.get(id=obj.id)


class SetupTestCase(TestCase):
    def test_setup_page(self):
        client = AuthenticatedClient()
        company = client.user.company
        ProductTypeFactory(company=company)
        IngredientTypeFactory(company=company)
        ContainerTypeFactory(company=company)
        r = client.get(reverse('setup'))
        self.assertContains(r, 'Blackberry and Thyme')
        self.assertContains(r, 'IngredType')
        self.assertContains(r, 'ContainerType')
