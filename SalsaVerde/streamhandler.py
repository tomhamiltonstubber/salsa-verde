import logging
from django.utils.termcolors import colorize
from functools import cached_property


class StreamHandler(logging.StreamHandler):  # pragma: no cover
    fg = {logging.DEBUG: 'blue', logging.INFO: 'cyan', logging.WARN: 'yellow'}

    @cached_property
    def is_tty(self):
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def format(self, record):
        message = super().format(record)
        if self.is_tty:
            fg = self.fg.get(record.levelno, 'red')
            message = colorize(message, fg=fg, opts=('bold',))
        return message
