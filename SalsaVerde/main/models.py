from datetime import datetime

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.forms import JSONField
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone


class UserManager(BaseUserManager):
    def _create_user(self, email, password, is_superuser=False, **extra_fields):
        """Create and save a User with the given email and password."""
        email = self.normalize_email(email)
        user = self.model(email=email, is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self.create_superuser(email, password, is_superuser=True, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField('Email Address', unique=True)
    first_name = models.CharField('First name', max_length=30, blank=True)
    last_name = models.CharField('Last name', max_length=150, blank=True)
    last_logged_in = models.DateTimeField('Last Logged in', default=datetime(2018, 1, 1))
    street = models.TextField('Street Address', null=True, blank=True)
    town = models.CharField('Town', max_length=50, null=True, blank=True)
    country = models.CharField('Country', max_length=50, null=True, blank=True)
    postcode = models.CharField('Postcode', max_length=20, null=True, blank=True)
    phone = models.CharField('Telephone Number', max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def has_document(self, doc_type):
        return self.focussed_documents.filter(doc_type=doc_type).exists()

    @staticmethod
    def model_form_fields():
        return ['email', 'first_name', 'last_name', 'street', 'town', 'country', 'postcode', 'phone']

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

    objects = UserManager()


class BaseModel(models.Model):
    objects = QuerySet.as_manager()

    class Meta:
        abstract = True


class NameBase(BaseModel):
    name = models.CharField('Name', max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Supplier(NameBase):
    street = models.TextField('Street Address', null=True, blank=True)
    town = models.CharField('Town', max_length=50, null=True, blank=True)
    country = models.CharField('Town', max_length=50, null=True, blank=True)
    postcode = models.CharField('Postcode', max_length=20, null=True, blank=True)
    phone = models.CharField('Telephone Number', max_length=255, null=True, blank=True)
    email = models.EmailField('Email', max_length=50, null=True, blank=True)
    main_contact = models.CharField('Main Contact', max_length=50, null=True, blank=True)

    @staticmethod
    def prefix():
        return 'suppliers'

    def get_absolute_url(self):
        return reverse(f'suppliers-details', kwargs={'pk': self.pk})

    @staticmethod
    def model_form_fields():
        return ['name', 'street', 'town', 'country', 'postcode', 'phone', 'email', 'main_contact']

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'


class IngredientType(NameBase):
    UNIT_KILO = 'kilogram'
    UNIT_LITRE = 'litre'
    UNIT_TYPES = (
        (UNIT_KILO, 'kg'),
        (UNIT_LITRE, 'litre'),
    )
    unit = models.CharField('Units', max_length=25, choices=UNIT_TYPES)


class Ingredient(BaseModel):
    STATUS_ACCEPT = 'accept'
    STATUS_HOLD = 'hold'
    STATUS_REJECT = 'reject'
    STATUS_CHOICES = (
        (STATUS_ACCEPT, 'Accept'),
        (STATUS_HOLD, 'Hold'),
        (STATUS_REJECT, 'Reject'),
    )
    ingredient_type = models.ForeignKey(IngredientType, related_name='ingredients', on_delete=models.CASCADE)
    batch_code = models.CharField('Batch Code', max_length=25)
    intake_date = models.DateTimeField('Intake Date')
    intake_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    condition = models.CharField('Condition', max_length=25, default='Good')
    supplier = models.ForeignKey(Supplier, related_name='ingredients', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField('Status', max_length=25, default=STATUS_ACCEPT)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=5)

    def get_absolute_url(self):
        return reverse('ingredient-details', kwargs={'pk': self.pk})

    def __str__(self):
        return '%s %s' % (self.ingredient_type, self.intake_date)

    @classmethod
    def prefix(cls):
        return 'ingredient'

    class Meta:
        verbose_name = 'Ingredient'


class ProductType(NameBase):
    ingredient_types = models.ManyToManyField(IngredientType, related_name='product_types')


class Product(BaseModel):
    product_type = models.ForeignKey(ProductType, related_name='products', on_delete=models.CASCADE)
    date_of_infusion = models.DateTimeField('Date of Infusion/Sous-vide', default=timezone.now)
    date_of_bottling = models.DateTimeField('Date of Infusion/Sous-vide', default=timezone.now)
    date_of_best_before = models.DateTimeField('Date of Best Before', default=timezone.now)

    product_ingredients = models.ManyToManyField('main.ProductIngredient', related_name='products')
    yield_quantity = models.DecimalField('Yield Quantity (in litres)', max_digits=25, decimal_places=25)
    yield_containers = models.ManyToManyField('main.YieldContainers', related_name='products')


class ProductIngredient(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=5)


class ContainerType(NameBase):
    TYPE_BOTTLE = 'bottle'
    TYPE_CAP = 'cap'
    TYPE_OTHER = 'other'
    TYPE_CONTAINERS = (
        (TYPE_BOTTLE, 'Bottle'),
        (TYPE_CAP, 'Cap'),
        (TYPE_OTHER, 'Container'),
    )
    size = models.DecimalField('Size', max_digits=25, decimal_places=5)
    type = models.CharField('Container Type', choices=TYPE_CONTAINERS, max_length=255)


class Container(BaseModel):
    container_type = models.ForeignKey(ContainerType, on_delete=models.CASCADE)
    batch_code = models.CharField('Batch Code', max_length=25)


class YieldContainers(models.Model):
    container = models.ForeignKey(Container, on_delete=models.CASCADE)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=5)


class Document(BaseModel):
    FORM_COM1 = 'com1'
    FORM_COM2 = 'com2'
    FORM_GL01 = 'gl01'
    FORM_GL02 = 'gl02'
    FORM_INT1 = 'int1'
    FORM_NC01 = 'nc01'
    FORM_PLA01 = 'pla01'
    FORM_ST01 = 'st01'
    FORM_ST02 = 'st02'
    FORM_ST03 = 'st03'
    FORM_ST04 = 'st04'
    FORM_SUP01 = 'sup01'
    FORM_SUP02 = 'sup02'
    FORM_SUP03 = 'sup03'
    FORM_SUP04 = 'sup04'
    FORM_TRA01 = 'tra01'
    FORM_VIS01 = 'vis01'

    FORM_TYPES = (
        (FORM_COM1, 'COM1 - Complaint Summary'),
        (FORM_COM2, 'COM2 - Complaint Log'),
        (FORM_GL01, 'GL01 - Glass Audit'),
        (FORM_GL02, 'GL02 - Glass Breakage Report'),
        (FORM_INT1, 'INT1 - Intake of Goods'),
        (FORM_NC01, 'NC01 - Non Conformity Report'),
        (FORM_PLA01, 'PLA01 - Plaster Log'),
        (FORM_ST01, 'ST01 - Staff Health Questionnaire'),
        (FORM_ST02, 'ST02 - Return to Work Questionnaire'),
        (FORM_ST03, 'ST03 - Induction Log'),
        (FORM_ST04, 'ST04 - Staff Training Record'),
        (FORM_SUP01, 'SUP01 - Raw Materials Suppliers'),
        (FORM_SUP02, 'SUP02 - Packaging Suppliers'),
        (FORM_SUP03, 'SUP03 - Service Suppliers'),
        (FORM_SUP04, 'SUP04 - Supplier Self Audit'),
        (FORM_TRA01, 'TRA01 - Traceability'),
        (FORM_VIS01, 'VIS01 - Visitor Questionnaire'),
    )

    date_created = models.DateTimeField('Date Created', auto_now_add=True)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='salsa_sheets')
    type = models.CharField('Salsa Form Type', max_length=6, blank=True, null=True, choices=FORM_TYPES)
    file = models.FileField(upload_to='static/documents/', null=True, max_length=256)
    focus = models.ForeignKey('main.User', null=True, related_name='focussed_documents', on_delete=models.SET_NULL)
    edits = JSONField()


class Area(NameBase):
    pass


class Complaint(Document):
    COMPLAINT_BACTERIA = 'bacteria'
    COMPLAINT_PACKAGING = 'packaging'
    COMPLAINT_FOREIGN = 'foreign'
    COMPLAINT_OTHER = 'other'
    COMPLAINT_TYPES = (
        (COMPLAINT_BACTERIA, 'Bacteria'),
        (COMPLAINT_PACKAGING, 'Packaging'),
        (COMPLAINT_FOREIGN, 'Foreign Body'),
        (COMPLAINT_OTHER, 'Other'),
    )

    complaint_type = models.CharField('Reason', choices=COMPLAINT_TYPES, max_length=255)
    affected_product = models.ManyToManyField(Product, related_name='complaints')
    complainant_name = models.CharField('Complainant Name', max_length=50)
    complainant_address = models.TextField('Complainant Address', max_length=255)
    complainant_phone = models.CharField('Complainant Phone', max_length=255, null=True, blank=True)
    method = models.CharField('Complainant Method', max_length=25)
    description = models.TextField('Complainant Description', max_length=255)

    investigator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    cause = models.TextField('Complaint Cause', max_length=255)
    corrective_action_desc = models.TextField('Corrective Action Desc', max_length=255)

    corrective_action_date = models.DateTimeField('Corrective Action Taken')
    complaint_reply_date = models.DateTimeField('Corrective Action Taken')


class GlassAudit(Document):
    audited_area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL)
    container = models.ForeignKey(Container, on_delete=models.CASCADE)
    broken_containers = models.PositiveSmallIntegerField('Broken Containers')
    action_taken = models.TextField('Action Taken', blank=True, default='')


class GlassBreakageReport(Document):
    breakage_area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField('Breakage Details')
    area_cleared = models.BooleanField('Area Cleared', default=True)


class PlasterReport(Document):
    recipient = models.ForeignKey(User, related_name='plaster_reports', on_delete=models.CASCADE)
    plaster_check_time = models.DateTimeField('Plaster Check Time')
    plaster_check_employee = models.ForeignKey(User, null=True, blank=True,
                                               on_delete=models.SET_NULL)
