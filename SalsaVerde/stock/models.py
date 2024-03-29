from decimal import Decimal

from django.db import models
from django.db.models import QuerySet
from django.forms import JSONField
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from SalsaVerde.company.models import BaseModel, CompanyNameBaseModel, User
from SalsaVerde.storage_backends import PrivateMediaStorage


class Supplier(CompanyNameBaseModel):
    street = models.TextField('Street Address', null=True, blank=True)
    town = models.CharField('Town', max_length=50, null=True, blank=True)
    county = models.CharField('County', max_length=50, null=True, blank=True)
    country = models.CharField('Country', max_length=50, null=True, blank=True)
    postcode = models.CharField('Postcode', max_length=20, null=True, blank=True)
    phone = models.CharField('Phone', max_length=255, null=True, blank=True)
    email = models.EmailField('Email', max_length=65, null=True, blank=True)
    main_contact = models.CharField('Main Contact', max_length=50, null=True, blank=True)
    contact_phone = models.CharField('Contact Phone', max_length=255, null=True, blank=True)
    vat_number = models.CharField('VAT Number', max_length=50, null=True, blank=True)
    company_number = models.CharField('Company Number', max_length=50, null=True, blank=True)

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
        return reverse('suppliers-details', kwargs={'pk': self.pk})

    class Meta:
        ordering = ('name',)
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
        return reverse('ingredient-types-details', kwargs={'pk': self.pk})

    class Meta:
        ordering = ('name',)
        verbose_name = 'Raw Ingredient Type'
        verbose_name_plural = 'Raw Ingredients Types'


class IngredientQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(ingredient_type__company=request.user.company)


def _display_dec(v: Decimal):
    if v == int(v):
        return int(v)
    return v


class Ingredient(BaseModel):
    objects = IngredientQuerySet.as_manager()

    ingredient_type = models.ForeignKey(
        IngredientType,
        verbose_name='Raw ingredient type',
        related_name='ingredients',
        on_delete=models.CASCADE,
        help_text='The type of raw ingredient',
    )
    batch_code = models.CharField(
        'Batch Code', max_length=25, help_text='The batch code of the raw ingredient on intake'
    )
    supplier = models.ForeignKey(
        Supplier,
        verbose_name='Supplier',
        related_name='ingredients',
        null=True,
        on_delete=models.SET_NULL,
        help_text='The supplier of the raw ingredient',
    )
    intake_quality_check = models.BooleanField('Accept goods', default=False)
    intake_quality_check.help_text = 'Goods are free from damage and pests'
    quantity = models.DecimalField(
        'Quantity', max_digits=25, decimal_places=3, help_text='The quantity of the raw ingredient on intake'
    )
    finished = models.BooleanField(
        'Finished', default=False, help_text='Whether the raw ingredient has been completely used'
    )

    intake_notes = models.TextField(
        'Intake Notes', null=True, blank=True, help_text='Any notes pertaining to the raw ingredient intake'
    )
    intake_user = models.ForeignKey(
        User,
        verbose_name='Intake Recipient',
        on_delete=models.CASCADE,
        null=True,
        help_text='The user who received the raw ingredient',
    )
    intake_date = models.DateTimeField(
        'Intake date', default=timezone.now, help_text='The date of the raw ingredient intake'
    )

    def get_absolute_url(self):
        return reverse('ingredients-details', kwargs={'pk': self.pk})

    def display_quantity(self):
        return f'{float(self.quantity):,g} {dict(IngredientType.UNIT_TYPES)[self.ingredient_type.unit]}s'

    def __str__(self):
        return mark_safe(f'{self.name} - {self.batch_code} - {self.intake_date:%d/%m/%Y}')

    @property
    def name(self):
        return self.ingredient_type.name

    @classmethod
    def prefix(cls):
        return 'ingredients'

    class Meta:
        ordering = ('ingredient_type__name',)
        verbose_name = 'Raw Ingredient'
        verbose_name_plural = 'Raw Ingredients'


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
    type = models.CharField('Packaging Type', choices=TYPE_CONTAINERS, max_length=255, default=TYPE_BOTTLE)

    @classmethod
    def prefix(cls):
        return 'container-types'

    def get_absolute_url(self):
        return reverse('container-types-details', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Packaging Type'
        verbose_name_plural = 'Packaging Types'


class ContainerQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(container_type__company=request.user.company)


class Container(BaseModel):
    objects = ContainerQuerySet.as_manager()

    container_type = models.ForeignKey(
        ContainerType,
        verbose_name='Packaging type',
        related_name='containers',
        on_delete=models.CASCADE,
        help_text='The type of packaging',
    )
    batch_code = models.CharField('Batch Code', max_length=25, help_text='The batch code of the packaging on intake')
    supplier = models.ForeignKey(
        Supplier,
        verbose_name='Supplier',
        related_name='containers',
        null=True,
        on_delete=models.SET_NULL,
        help_text='The supplier of the packaging',
    )
    intake_quality_check = models.BooleanField('Accept goods', default=False)
    intake_quality_check.help_text = 'Goods are free from damage and pests'
    quantity = models.DecimalField(
        'Quantity', max_digits=25, decimal_places=3, help_text='The quantity of the packaging on intake'
    )
    finished = models.BooleanField(
        'Finished', default=False, help_text='Whether the packaging has been completely used'
    )

    intake_notes = models.TextField(
        'Intake Notes', null=True, blank=True, help_text='Any notes pertaining to the packaging intake'
    )
    intake_user = models.ForeignKey(
        User,
        verbose_name='Intake Recipient',
        on_delete=models.CASCADE,
        null=True,
        help_text='The user who received the packaging',
    )
    intake_date = models.DateTimeField(
        'Intake date', default=timezone.now, help_text='The date of the packaging intake'
    )

    @classmethod
    def prefix(cls):
        return 'containers'

    def display_quantity(self):
        return f'{float(self.quantity):,g} {dict(ContainerType.TYPE_CONTAINERS)[self.container_type.type]}s'

    def get_absolute_url(self):
        return reverse('containers-details', kwargs={'pk': self.pk})

    def __str__(self):
        return mark_safe(f'{self.name} - {self.batch_code}')

    @property
    def name(self):
        return self.container_type.name

    class Meta:
        verbose_name = 'Packaging'
        verbose_name_plural = 'Packaging'


class YieldContainerQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(product__product_type__company=request.user.company)


class YieldContainer(BaseModel):
    objects = YieldContainerQuerySet.as_manager()

    product = models.ForeignKey(
        'stock.Product', verbose_name='Product', related_name='yield_containers', on_delete=models.CASCADE
    )
    container = models.ForeignKey(Container, related_name='yield_containers', on_delete=models.CASCADE)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=3)
    user = models.ForeignKey(User, verbose_name='User', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField('Date', default=timezone.now)

    def get_absolute_url(self):
        return self.container.get_absolute_url()

    def display_quantity(self):
        return f'{float(self.quantity):,g} {dict(ContainerType.TYPE_CONTAINERS)[self.container.container_type.type]}s'

    @property
    def total_volume(self):
        if self.container.container_type.size:
            return self.quantity * self.container.container_type.size

    def display_total_volume(self):
        return f'{float(self.total_volume):,g} litres'


class ProductType(CompanyNameBaseModel):
    ingredient_types = models.ManyToManyField(IngredientType, verbose_name='Ingredients', related_name='product_types')
    code = models.CharField('Code', max_length=3, help_text='2 or 3 letter code for batch code creation')

    @classmethod
    def prefix(cls):
        return 'product-types'

    def get_absolute_url(self):
        return reverse('product-types-details', kwargs={'pk': self.pk})

    def display_ingredient_types(self):
        return ', '.join(self.ingredient_types.values_list('name', flat=True).order_by('name'))

    class Meta:
        ordering = ('name',)
        verbose_name = 'Product Type'
        verbose_name_plural = 'Product Types'


class ProductTypeSizeQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(product_type__company=request.user.company)


class ProductTypeSize(models.Model):
    objects = ProductTypeSizeQuerySet.as_manager()

    product_type = models.ForeignKey(ProductType, related_name='product_type_sizes', on_delete=models.CASCADE)
    sku_code = models.CharField('SKU Code', max_length=25, null=True, blank=True)
    bar_code = models.CharField('Bar Code', max_length=40, null=True, blank=True)
    size = models.DecimalField('Container Size in litres', decimal_places=3, max_digits=8)
    name = models.CharField('Name', max_length=40, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('product-type-sizes-edit', kwargs={'pk': self.pk})

    @classmethod
    def prefix(cls):
        return 'product-type-sizes'


class ProductQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(product_type__company=request.user.company)


class Product(BaseModel):
    STATUS_INFUSED = 'infused'
    STATUS_BOTTLED = 'bottled'
    STATUSES = (
        (STATUS_INFUSED, 'Infused'),
        (STATUS_BOTTLED, 'Bottled'),
    )

    objects = ProductQuerySet.as_manager()

    product_type = models.ForeignKey(
        ProductType, verbose_name='Product', related_name='products', on_delete=models.CASCADE
    )
    date_of_infusion = models.DateTimeField('Date of Production', default=timezone.now)
    date_of_bottling = models.DateTimeField('Date of Bottling', default=timezone.now, null=True, blank=True)
    date_of_best_before = models.DateTimeField('Date of Best Before', default=timezone.now, null=True, blank=True)

    yield_quantity = models.DecimalField('Yield Quantity', max_digits=25, decimal_places=3, null=True, blank=True)
    batch_code = models.CharField('Batch Code', max_length=25, null=True, blank=True)

    status = models.CharField('Stage', choices=STATUSES, max_length=25)

    batch_code_applied = models.BooleanField('Batch code applied', default=False)
    best_before_applied = models.BooleanField('Best before applied', default=False)
    quality_check_successful = models.BooleanField('Quality check successful', default=False)
    finished = models.BooleanField('Finished', default=False)

    def display_yield_quantity(self):
        return f'{float(self.yield_quantity or 0):,g} litres'

    def __str__(self):
        return f'{self.product_type} - {self.batch_code}'

    def get_absolute_url(self):
        return reverse('products-details', kwargs={'pk': self.pk})

    @classmethod
    def prefix(cls):
        return 'products'

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ('product_type__name',)


class ProductIngredientQuerySet(QuerySet):
    def request_qs(self, request):
        return self.filter(product__product_type__company=request.user.company)


class ProductIngredient(BaseModel):
    objects = ProductIngredientQuerySet.as_manager()

    product = models.ForeignKey(
        Product, verbose_name='Product', on_delete=models.CASCADE, related_name='product_ingredients'
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField('Quantity', max_digits=25, decimal_places=3)

    def get_absolute_url(self):
        return self.ingredient.get_absolute_url()

    def display_quantity(self):
        return f'{float(self.quantity):,g} {dict(IngredientType.UNIT_TYPES)[self.ingredient.ingredient_type.unit]}'


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
    author = models.ForeignKey(
        User, verbose_name='Author', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents'
    )
    type = models.CharField('Salsa Form Type', max_length=6, blank=True, null=True, choices=FORM_TYPES)
    file = models.FileField(storage=PrivateMediaStorage(), blank=True, null=False, max_length=256)
    order = models.ForeignKey('orders.Order', related_name='labels', null=True, blank=True, on_delete=models.SET_NULL)
    focus = models.ForeignKey(
        User,
        verbose_name='Associated with',
        null=True,
        blank=True,
        related_name='focused_documents',
        on_delete=models.SET_NULL,
    )
    supplier = models.ForeignKey(
        Supplier,
        verbose_name='Linked Supplier',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='documents',
    )
    edits = JSONField()

    def __str__(self):
        if self.file:
            return self.file.name
        return f'{self.display_type()} - {self.date_created.date()}'

    @property
    def name(self):
        return str(self)

    def get_absolute_url(self):
        return reverse('documents-details', kwargs={'pk': self.pk})

    @classmethod
    def prefix(cls):
        return 'documents'

    def display_type(self):
        if self.type:
            return dict(self.FORM_TYPES)[self.type]

    def display_supplier(self):
        if self.supplier:
            return link(self.supplier.get_absolute_url(), str(self.supplier))

    def display_file(self):
        if self.file:
            return link(self.file.url, self.file.name)
        return '—'

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-date_created']


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
    plaster_check_employee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)


def link(link, name):
    return mark_safe(f'<a href="{link}">{name}</a>')
