import sys
import logging


class log:
    class levels:
        NONE = 0
        INFO = 1
        DEBUG = 2

    def __init__(self, scope_id = None):
        self.id = scope_id

    @staticmethod
    def enable(level = levels.INFO):
        logging.basicConfig()
        log.set_level(level)

    @staticmethod
    def set_level(level):
        logging.getLogger().setLevel({
            log.levels.NONE: logging.NOTSET,
            log.levels.INFO: logging.INFO,
            log.levels.DEBUG: logging.DEBUG
        }.get(level))

    def fmt(self, string):
        return f'[{self.id}] {string}'

    def info(self, string): return logging.info(self.fmt(string))
    def err(self, string): return logging.error(self.fmt(string))
    def warn(self, string): return logging.warning(self.fmt(string))
    def debug(self, string): return logging.debug(self.fmt(string))
    def dump(self, obj, pretty = True):
        self.debug(f'object dumped. len %d' % len(obj))
        self.debug(obj if not pretty else
                __import__('pprint').pformat(obj, indent = 4))

    def fatal(self, string):
        self.err(self.fmt(string))
        sys.exit(1)
