import factory
from django.db import IntegrityError

from SalsaVerde.stock.factories.company import CompanyFactory
from SalsaVerde.stock.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    password = 'testing'
    company = factory.SubFactory(CompanyFactory)
    first_name = 'Jane'
    last_name = factory.Sequence(lambda n: 'Doe%d' % n)
    phone = factory.Sequence(lambda n: '01264 ' + ('%02d' % n)[:2] * 3)

    street = factory.LazyAttribute(lambda u: '%s House, Any Street' % u.last_name)
    town = factory.LazyAttribute(lambda u: '%sville' % u.last_name)
    postcode = 'PO37 50DE'
    administrator = True

    @factory.LazyAttribute
    def email(self):
        fn = getattr(self, 'first_name', 'Jane')
        ln = self.last_name
        em = '%s_%s@example.com' % (fn, ln)
        return em.lower().replace(' ', '_')

    @classmethod
    def _create(cls, model_class, n=0, *args, **kwargs):
        """
        Override the default ``_create`` with our custom call.
        The default would use ``manager.create(*args, **kwargs)``
        """
        manager = cls._get_manager(model_class)

        try:
            user = manager.create_user(*args, **kwargs)
        except IntegrityError:
            kwargs.update(email=f"{kwargs['email']}{n}")
            n += 1
            cls._create(model_class, n, *args, **kwargs)
        else:
            return user
