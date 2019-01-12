from datetime import datetime as dt

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from SalsaVerde.main.models import User
from SalsaVerde.main.tests.test_common import AuthenticatedClient, refresh


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
