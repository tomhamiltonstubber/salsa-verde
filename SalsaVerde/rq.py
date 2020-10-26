import logging

from rq.utils import ColorizingStreamHandler


class RQHandler(ColorizingStreamHandler):
    def format(self, record):  # pragma: no cover
        message = logging.StreamHandler.format(self, record)
        if self.is_tty:
            colorize = self.levels.get(record.levelno, lambda x: x)

            # Don't colorize any traceback
            parts = message.split('\n', 1)
            parts[0] = colorize(parts[0])
            message = '\n'.join(parts)

        return message
