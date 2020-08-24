import factory

from SalsaVerde.company.models import Company, Country


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Country

    name = 'Greater Britain'
    iso_2 = 'GB'


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: 'company %d' % n)
    country = factory.SubFactory(CountryFactory)
    street = '123 Fake Street'
    town = 'Portafake'
    postcode = '123abc'
    phone = '998877'
