from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.forms import JSONField
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from SalsaVerde.storage_backends import PrivateMediaStorage


class Company(models.Model):
    name = models.CharField('Name', max_length=255)

    def __str__(self):
        return self.name


class CompanyQuerySet(QuerySet):
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
    objects = CompanyQuerySet.as_manager()

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
    objects = UserManager.from_queryset(CompanyQuerySet)()

    company = models.ForeignKey(Company, verbose_name='Company', on_delete=models.CASCADE)

    username = None
    email = models.EmailField('Email Address', unique=True)
    first_name = models.CharField('First name', max_length=30, blank=True)
    last_name = models.CharField('Last name', max_length=150, blank=True)
    last_logged_in = models.DateTimeField('Last Logged in', default=datetime(2018, 1, 1, tzinfo=timezone.utc))
    street = models.TextField('Street Address', null=True, blank=True)
    town = models.CharField('Town', max_length=50, null=True, blank=True)
    country = models.CharField('Country', max_length=50, null=True, blank=True)
    postcode = models.CharField('Postcode', max_length=20, null=True, blank=True)
    phone = models.CharField('Phone', max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def has_document(self, doc_type):
        return self.focused_documents.filter(doc_type=doc_type).exists()

    def display_name(self):
        return str(self)

    def display_address(self):
        address = [a for a in [self.street, self.town, self.postcode, self.country] if a]
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


class Supplier(CompanyNameBaseModel):
    street = models.TextField('Street Address', null=True, blank=True)
    town = models.CharField('Town', max_length=50, null=True, blank=True)
    country = models.CharField('Country', max_length=50, null=True, blank=True)
    postcode = models.CharField('Postcode', max_length=20, null=True, blank=True)
    phone = models.CharField('Phone', max_length=255, null=True, blank=True)
    email = models.EmailField('Email', max_length=65, null=True, blank=True)
    main_contact = models.CharField('Main Contact', max_length=50, null=True, blank=True)

    def display_email(self):
        if self.email:
            return mark_safe(f'<a href="mailto:{self.email}">{self.email}</a>')
        return '–'

    def display_phone(self):
        if self.phone:
            return mark_safe(f'<a href="tel:{self.phone}">{self.phone}</a>')
        return '–'

    def display_address(self):
        address = [a for a in [self.street, self.town, self.postcode, self.country] if a]
        return ', '.join(address) or '–'

    @staticmethod
    def prefix():
        return 'suppliers'

    def get_absolute_url(self):
        return reverse(f'suppliers-details', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'


class IngredientType(CompanyNameBaseModel):
    UNIT_KILO = 'kilogram'
    UNIT_LITRE = 'litre'
    UNIT_TYPES = (
        (UNIT_KILO, 'kg'),
        (UNIT_LITRE, 'litre'),
    )
    unit = models.CharField('Units', max_length=25, choices=UNIT_TYPES, help_text='Ingredient is measured in?')

    @classmethod
    def prefix(cls):
        return 'ingredient-types'

    def get_absolute_url(self):
        return reverse(f'ingredient-types-details', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Ingredient Type'
        verbose_name_plural = 'Ingredients Types'


class IngredientQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(ingredient_type__company=request.user.company)


class Ingredient(BaseModel):
    STATUS_ACCEPT = 'accept'
    STATUS_HOLD = 'hold'
    STATUS_REJECT = 'reject'
    STATUS_CHOICES = (
        (STATUS_ACCEPT, 'Accept'),
        (STATUS_HOLD, 'Hold'),
        (STATUS_REJECT, 'Reject'),
    )
    ingredient_type = models.ForeignKey(IngredientType, verbose_name='Ingredient Type',
                                        related_name='ingredients', on_delete=models.CASCADE)
    batch_code = models.CharField('Batch Code', max_length=25)
    condition = models.CharField('Condition', max_length=25, default='Good')
    supplier = models.ForeignKey(Supplier, verbose_name='Supplier', related_name='ingredients',
                                 null=True, on_delete=models.SET_NULL)
    status = models.CharField('Status', max_length=25, default=STATUS_ACCEPT, choices=STATUS_CHOICES)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=3)
    goods_intake = models.ForeignKey('main.GoodsIntake', related_name='ingredients', verbose_name='Goods Intake',
                                     on_delete=models.CASCADE)

    objects = IngredientQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse('ingredients-details', kwargs={'pk': self.pk})

    def display_quantity(self):
        return f'{self.quantity} {dict(IngredientType.UNIT_TYPES)[self.ingredient_type.unit]}'

    def __str__(self):
        return mark_safe(f'{self.name} - {self.batch_code}')

    @property
    def name(self):
        return self.ingredient_type.name

    @property
    def intake_document(self):
        return self.goods_intake.intake_document

    @classmethod
    def prefix(cls):
        return 'ingredients'

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'


class ContainerType(CompanyNameBaseModel):
    TYPE_BOTTLE = 'bottle'
    TYPE_CAP = 'cap'
    TYPE_OTHER = 'other'
    TYPE_CONTAINERS = (
        (TYPE_BOTTLE, 'Bottle'),
        (TYPE_CAP, 'Cap'),
        (TYPE_OTHER, 'Container'),
    )
    size = models.DecimalField('Size', max_digits=25, null=True, blank=True, decimal_places=3)
    type = models.CharField('Container Type', choices=TYPE_CONTAINERS, max_length=255, default=TYPE_BOTTLE)

    @classmethod
    def prefix(cls):
        return 'container-types'

    def get_absolute_url(self):
        return reverse(f'container-types-details', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Container Type'
        verbose_name_plural = 'Container Types'


class ContainerQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(container_type__company=request.user.company)


class Container(BaseModel):
    STATUS_ACCEPT = 'accept'
    STATUS_HOLD = 'hold'
    STATUS_REJECT = 'reject'
    STATUS_CHOICES = (
        (STATUS_ACCEPT, 'Accept'),
        (STATUS_HOLD, 'Hold'),
        (STATUS_REJECT, 'Reject'),
    )
    objects = ContainerQuerySet.as_manager()

    container_type = models.ForeignKey(ContainerType, verbose_name='Container', on_delete=models.CASCADE)
    batch_code = models.CharField('Batch Code', max_length=25)
    condition = models.CharField('Condition', max_length=25, default='Good')
    supplier = models.ForeignKey(Supplier, verbose_name='Supplier', related_name='containers',
                                 null=True, on_delete=models.SET_NULL)
    status = models.CharField('Status', max_length=25, default=STATUS_ACCEPT, choices=STATUS_CHOICES)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=3)
    goods_intake = models.ForeignKey('main.GoodsIntake', related_name='containers', verbose_name='Goods Intake',
                                     on_delete=models.CASCADE)

    @classmethod
    def prefix(cls):
        return 'containers'

    def get_absolute_url(self):
        return reverse(f'containers-details', kwargs={'pk': self.pk})

    def __str__(self):
        return mark_safe(f'{self.name} - {self.batch_code}')

    @property
    def intake_document(self):
        return self.goods_intake.intake_document

    @property
    def name(self):
        return self.container_type.name

    class Meta:
        verbose_name = 'Container'
        verbose_name_plural = 'Container'


class YieldContainer(BaseModel):
    product = models.ForeignKey('main.Product', verbose_name='Product', related_name='yield_containers',
                                on_delete=models.CASCADE)
    container = models.ForeignKey(Container, related_name='yield_containers', on_delete=models.CASCADE)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=3)

    def get_absolute_url(self):
        return self.product.get_absolute_url()


class GoodsIntakeQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(intake_user__company=request.user.company)


class GoodsIntake(BaseModel):
    objects = GoodsIntakeQuerySet.as_manager()

    date_created = models.DateTimeField('Date created', default=timezone.now)
    intake_date = models.DateTimeField('Intake date', default=timezone.now)
    intake_user = models.ForeignKey(User, verbose_name='Intake Recipient', on_delete=models.CASCADE)

    def display_intake_date(self):
        return self.intake_date.strftime(settings.DT_FORMAT)

    @property
    def intake_document(self):
        try:
            return Document.objects.get(goods_intake=self)
        except Document.DoesNotExist:
            return


class ProductType(CompanyNameBaseModel):
    ingredient_types = models.ManyToManyField(IngredientType, verbose_name='Ingredients', related_name='product_types')
    sku_code = models.CharField('SKU Code', max_length=25)
    code = models.CharField('Code', max_length=3, help_text='2 or 3 letter code for batch code creation')

    @classmethod
    def prefix(cls):
        return 'product-types'

    def get_absolute_url(self):
        return reverse(f'product-types-details', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Product Type'
        verbose_name_plural = 'Product Types'


class ProductQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(product_type__company=request.user.company)


class Product(BaseModel):
    objects = ProductQuerySet.as_manager()

    product_type = models.ForeignKey(ProductType, verbose_name='Product', related_name='products',
                                     on_delete=models.CASCADE)
    date_of_infusion = models.DateTimeField('Date of Infusion/Sous-vide', default=timezone.now)
    date_of_bottling = models.DateTimeField('Date of Bottling', default=timezone.now)
    date_of_best_before = models.DateTimeField('Date of Best Before', default=timezone.now)

    yield_quantity = models.DecimalField('Yield Quantity (in litres)', max_digits=25, decimal_places=3)
    batch_code = models.CharField('Batch Code', max_length=25)

    def __str__(self):
        return f'{self.product_type} - {self.batch_code}'

    def get_absolute_url(self):
        return reverse(f'products-details', kwargs={'pk': self.pk})

    @classmethod
    def prefix(cls):
        return 'products'

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


class ProductIngredient(BaseModel):
    product = models.ForeignKey(Product, verbose_name='Product', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=3)


class DocumentQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(author__company=request.user.company)


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

    objects = DocumentQuerySet.as_manager()

    date_created = models.DateTimeField('Date Created', auto_now_add=True)
    author = models.ForeignKey(User, verbose_name='Author', null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='documents')
    type = models.CharField('Salsa Form Type', max_length=6, blank=True, null=True, choices=FORM_TYPES)
    file = models.FileField(storage=PrivateMediaStorage(), blank=True, null=False, max_length=256)
    focus = models.ForeignKey('main.User', verbose_name='Associated with', null=True, related_name='focused_documents',
                              on_delete=models.SET_NULL)
    goods_intake = models.ForeignKey('main.GoodsIntake', verbose_name='Intake of Goods', null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='documents')
    edits = JSONField()

    def __str__(self):
        return f'{self.display_type()} - {self.date_created.date()}'

    def get_absolute_url(self):
        return reverse('documents-details', kwargs={'pk': self.pk})

    @classmethod
    def prefix(cls):
        return 'documents'

    def display_type(self):
        return dict(self.FORM_TYPES)[self.type]

    def display_file(self):
        if self.file:
            return mark_safe(f'<a href="{self.file.url}" target="_blank">{self.file.name}</a>')
        return '—'

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'


class Area(CompanyNameBaseModel):
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
