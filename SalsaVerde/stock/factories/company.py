import factory

from SalsaVerde.stock.models import Company


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: 'company %d' % n)
