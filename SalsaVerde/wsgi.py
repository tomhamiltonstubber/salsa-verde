import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SalsaVerde.settings")

from django.core.wsgi import get_wsgi_application  # noqa
from whitenoise.django import DjangoWhiteNoise  # noqa

application = get_wsgi_application()
application = DjangoWhiteNoise(application)
