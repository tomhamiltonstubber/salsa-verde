import os
import re

from django.conf import settings
from django.core.management import BaseCommand
from grablib import Grab, setup_logging

STATIC_DIR = os.path.join(settings.BASE_DIR, 'static')
SCSS_DIR = os.path.join(STATIC_DIR, 'scss')
CSS_DIR = os.path.join(STATIC_DIR, 'css')


class Command(BaseCommand):
    help = 'watch and build scss files'

    def handle(self, **kwargs):
        setup_logging('INFO')
        self.verbosity = kwargs['verbosity']

        self._log('\nwatching %s\n\n' % SCSS_DIR, level=0)

        self._build()

        import pyinotify

        wm = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(wm, self._handle_event)

        mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_TO
        wm.add_watch(SCSS_DIR, mask, rec=True, auto_add=True)
        notifier.loop()

    def _handle_event(self, event):
        if not re.match('.*\.s?css$', event.name):
            return
        self._build()

    def _build(self):
        grab = Grab('grablib.yml', debug=True)
        grab.build()

    def _log(self, msg, level=1):
        if self.verbosity >= level:
            self.stdout.write(msg)
