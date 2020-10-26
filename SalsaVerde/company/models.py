from datetime import datetime, timezone

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse


class CountryQueryset(QuerySet):
    def request_qs(self, request):
        return Country.objects.all()


class Country(models.Model):
    objects = CountryQueryset.as_manager()

    name = models.CharField('Name', max_length=255)
    iso_2 = models.CharField('2 Letter ISO', max_length=2)
    iso_3 = models.CharField('3 Letter ISO', max_length=3)

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField('Name', max_length=255)
    website = models.CharField(max_length=255, blank=True)
    dhl_account_code = models.CharField(max_length=255, blank=True)
    main_contact = models.ForeignKey(
        'company.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_company'
    )
    shopify_domain = models.CharField(null=True, blank=True, max_length=255)
    shopify_webhook_key = models.CharField(null=True, blank=True, max_length=255)
    shopify_api_key = models.CharField(null=True, blank=True, max_length=255)
    shopify_password = models.CharField(null=True, blank=True, max_length=255)

    street = models.TextField('Street Address', null=True, blank=True)
    town = models.CharField('Town', max_length=50, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    postcode = models.CharField('Postcode', max_length=20, null=True, blank=True)
    phone = models.CharField('Phone', max_length=255, null=True, blank=True)

    def get_main_contact(self):
        if not self.main_contact:
            self.main_contact = self.users.first()
            self.save()
        return self.main_contact

    def __str__(self):
        return self.name


class CompanyQueryset(QuerySet):
    def request_qs(self, request):
        return self.filter(company=request.user.company)


class NoQS(QuerySet):
    def request_qs(self, request):
        raise NotImplementedError


class BaseModel(models.Model):
    objects = NoQS.as_manager()

    class Meta:
        abstract = True


class CompanyNameBaseModel(BaseModel):
    name = models.CharField('Name', max_length=255)
    company = models.ForeignKey(Company, verbose_name='Company', on_delete=models.CASCADE)
    objects = CompanyQueryset.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def _create_user(self, email, company, password, is_superuser=False, **extra_fields):
        """Create and save a User with the given email and password."""
        email = self.normalize_email(email)
        user = self.model(email=email, is_superuser=is_superuser, company=company, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, company, password=None, **extra_fields):
        return self._create_user(email, company, password, **extra_fields)

    def create_superuser(self, email, company, password, **extra_fields):
        return self.create_superuser(email, company, password, is_superuser=True, **extra_fields)


class User(AbstractUser):
    objects = UserManager.from_queryset(CompanyQueryset)()

    company = models.ForeignKey(Company, verbose_name='Company', on_delete=models.CASCADE, related_name='users')

    username = None
    email = models.EmailField('Email Address', unique=True)
    first_name = models.CharField('First name', max_length=30, blank=True)
    last_name = models.CharField('Last name', max_length=150, blank=True)
    last_logged_in = models.DateTimeField('Last Logged in', default=datetime(2018, 1, 1, tzinfo=timezone.utc))
    street = models.TextField('Street Address', null=True, blank=True)
    town = models.CharField('Town', max_length=50, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    postcode = models.CharField('Postcode', max_length=20, null=True, blank=True)
    phone = models.CharField('Phone', max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def has_document(self, doc_type):
        return self.focused_documents.filter(doc_type=doc_type).exists()

    def display_name(self):
        return str(self)

    def display_address(self):
        address = [a for a in [self.street, self.town, self.postcode] if a]
        return ', '.join(address) or '–'

    def get_absolute_url(self):
        return reverse('users-details', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @staticmethod
    def prefix():
        return 'users'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
