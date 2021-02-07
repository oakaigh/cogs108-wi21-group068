import sys
import logging
import threading
import datetime

# TODO
import dateutil.parser
import isodate

class formats:
    class time:
        UNIX = 0
        ISO8601 = 1

class decode:
    @staticmethod
    def unexpected(data, t):
        return data == None or isinstance(data, t)

    @staticmethod
    def time(data, format = formats.time.UNIX):
        if decode.unexpected(data, datetime.datetime):
            return data

        try:
            return {
                formats.time.UNIX:
                    lambda data: datetime.datetime.fromtimestamp(decode.integer(data)),
                formats.time.ISO8601:
                    lambda data: dateutil.parser.isoparse(data)
            }.get(format, lambda data: None)(data)
        except:
            return None

    @staticmethod
    def timedelta(data, format = formats.time.UNIX):
        if decode.unexpected(data, datetime.timedelta):
            return data

        try:
            return {
                formats.time.UNIX:
                    lambda data:
                        datetime.timedelta(
                            seconds = decode.integer(data)
                        ),
                formats.time.ISO8601:
                    lambda data: isodate.parse_duration(data)
            }.get(format, lambda data: None)(data)
        except:
            return None

    @staticmethod
    def integer(data):
        if decode.unexpected(data, int):
            return data
        try: return int(data)
        except: return None

class dtypes:
    string = None
    raw = string
    integer = decode.integer
    time = decode.time
    duration = decode.timedelta

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

class thread:
    pool = []

    @staticmethod
    def start(threads):
        for t in threads:
            t.start()
            thread.pool.append(t)

    @staticmethod
    def join():
        for t in thread.pool:
            t.join()

class merge:
    @staticmethod
    def dictlist(dicts: list) -> dict:
        ret = None
        for d in dicts:
            if d:
                if not ret:
                    ret = dict()
                ret.update(d)
        return ret

    @staticmethod
    def dicts(*args) -> dict:
        return merge.dictlist(list(args))

    @staticmethod
    def translate(templ: dict, trans: dict) -> dict:
        if not (isinstance(templ, dict) and \
                isinstance(trans, dict)):
            return

        for (k_templ, k_trans) in zip(templ, trans):
            o_trans = trans[k_trans]
            if isinstance(o_trans, dict):
                merge.translate(templ[k_templ], o_trans)
            elif callable(o_trans):
                templ[k_templ] = o_trans() if o_trans else None

        return templ

class select:
    @staticmethod
    def fromdict(o: dict, renamed_keys: dict, encoder = None):
        if o == None:
            return None

        ret = {}
        for old_k, new_k in renamed_keys.items():
            v = o.get(old_k)
            if v == None:
                continue
            if isinstance(new_k, dict):
                ret[old_k] = select.fromdict(v, new_k, encoder)
            else:
                ret[new_k or old_k] = v if not encoder else encoder(v)

        return ret

    @staticmethod
    def descend(o: dict, keys: list):
        curr_v = o
        for k in keys:
            if not isinstance(curr_v, dict):
                return curr_v
            curr_v = curr_v.get(k)
            if curr_v == None:
                break
        return curr_v
