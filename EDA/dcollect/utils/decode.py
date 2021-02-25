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

    @staticmethod
    def any(data, handler = None):
        return handler(data) if handler else data

    @staticmethod
    def array(data, handler = None):
        if decode.unexpected(data, list):
            return None
        ret = []
        for el in data:
            ret.append(any(el, handler = handler))
        return ret

class dtypes:
    any = decode.any
    array = decode.array
    string = None
    raw = string
    integer = decode.integer
    time = decode.time
    duration = decode.timedelta
