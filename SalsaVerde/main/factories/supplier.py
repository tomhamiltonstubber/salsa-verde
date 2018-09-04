import factory

from SalsaVerde.main.factories.company import CompanyFactory
from SalsaVerde.main.models import Supplier


class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Supplier

    company = factory.SubFactory(CompanyFactory)

    name = factory.Sequence(lambda n: 'Supplier%d' % n)
    street = factory.LazyAttribute(lambda u: '%s Factory, Any Lane' % u.name)
    town = factory.LazyAttribute(lambda u: '%sindus' % u.name)
    country = factory.LazyAttribute(lambda u: '%sland' % u.name)
    postcode = 'SUP01 IND01'
    phone = factory.Sequence(lambda n: '01264 ' + ('%02d' % n)[:2] * 3)
    main_contact = factory.Sequence(lambda n: 'Contact%s' % n)

    @factory.LazyAttribute
    def email(self):
        return '%s_%s@example.com' % (self.name, 'supplier')
