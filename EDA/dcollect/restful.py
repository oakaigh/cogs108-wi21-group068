from .utils import ds
from .utils import http

import typing

class utils:
    class directives:
        @staticmethod
        def reduce(directives, want):
            return ds.deep_update(
                source = want,
                overrides = directives,
                inplace = False,
                intersect = True
            ) if want else directives

        @staticmethod
        def compile(dtype, directives):
            class _ret_type(dtype):
                def __new__(cls, data):
                    return dtype.__call__(
                        data = data,
                        directives = directives
                    )
            return _ret_type

        @staticmethod
        def parse_entry(directives_entry) -> tuple:
            keys, args, filter_fn = None, None, None

            if isinstance(directives_entry, tuple):
                if len(directives_entry) == 2:
                    keys, args = directives_entry
                elif len(directives_entry) == 3:
                    keys, args, filter_fn = directives_entry
            else:
                keys = directives_entry

            if keys and not isinstance(keys, list):
                keys = [keys]
            if not args:
                args = {}

            return keys, args, filter_fn

        @staticmethod
        def traversal(directives):
            for k, v in directives.items():
                if isinstance(v, dict):
                    yield from utils.directives.traversal(v)
                else:
                    keys, args, filter_fn = utils.directives.parse_entry(v)
                    yield k, keys, args, filter_fn

class types:
    string = str
    integer = int

    any = None

    @staticmethod
    def custom(default = any):
        class _custom:
            def __new__(cls, data, t = None, args = {}):
                _t = t or default
                return _t(data, **args) if _t else data

        return _custom

    class region:
        US = 'us'

    class video:
        class formats:
            UNKNOWN = -1
            SD = 0
            HD = 1

            def __init__(self,
                data: str, format = None
            ):
                data = data.lower()
                defs = {
                    types.video.formats.SD: {
                        'sd',
                        '96p',
                        '120p', '144p', '180p',
                        '240i', '240p', '288i', '288p', '272p',
                        '360p',
                        '480i', '480p',
                        '576i', '576p'
                    },
                    types.video.formats.HD: [
                        'hd',
                        '720p',
                        '1080i', '1080p'
                    ]
                }

                self._ = types.video.formats.UNKNOWN
                for d, dstrs in defs.items():
                    if data in dstrs:
                        self._ = d

            def __str__(self):
                return {
                    types.video.formats.UNKNOWN: 'UNKNOWN',
                    types.video.formats.SD: 'SD',
                    types.video.formats.HD: 'HD'
                }.get(self._)

            def __repr__(self):
                return f"video.formats.{self.__str__()}"

    class time:
        import datetime

        # TODO
        import dateutil.parser
        import isodate

        class formats:
            UNIX = 0
            ISO8601 = 1

        class absolute(datetime.datetime):
            def __new__(cls,
                data,#: typing.Union[types.string, types.integer],
                format#: types.time.formats
            ):
                return {
                    types.time.formats.UNIX:
                        lambda: types.time.datetime.datetime.fromtimestamp(types.integer(data)),
                    types.time.formats.ISO8601:
                        lambda: types.time.dateutil.parser.isoparse(types.string(data))
                }.get(format, lambda: None)()

        class relative(datetime.timedelta):
            def __new__(cls,
                data,#: typing.Union[types.string, types.integer],
                format#: types.time.formats
            ):
                return {
                    types.time.formats.UNIX:
                        lambda:
                            types.time.datetime.timedelta(
                                seconds = types.integer(data)
                            ),
                    types.time.formats.ISO8601:
                        lambda: types.time.isodate.parse_duration(data)
                }.get(format, lambda: None)()

    class json:
        @staticmethod
        def array(elclass: type, iterator = False):
            class _iter:
                def __new__(cls, data: list, *args, **kwargs):
                    if isinstance(data, list):
                        for el in data:
                            yield elclass.__call__(el, *args, **kwargs)
            class _array:
                def __new__(cls, data: list, *args, **kwargs):
                    return list(_iter.__new__(cls, data, *args, **kwargs))

            return _iter if iterator else _array

        class object(dict):
            def __new__(cls,
                data: dict,
                directives: dict,
                classes: dict
            ):
                if not all((directives, classes)):
                    return data

                def decode(
                    directives: dict,
                    classes: dict
                ):
                    ret = {}

                    for k, v in directives.items():
                        if isinstance(v, dict):
                            ret[k] = decode(
                                directives = v,
                                classes = classes.get(k)
                            )
                        else:
                            keys, args, filter_fn = utils.directives.parse_entry(v)

                            _data = ds.select.descend(o = data, keys = keys) if keys else data
                            _class = ds.select.descend(o = classes, keys = [k])

                            if not all((_data, _class)):
                                ret[k] = None
                                continue

                            try:
                                if filter_fn:
                                    _data = filter_fn(_data)
                                ret[k] = _class(_data, **args) \
                                    if not isinstance(_data, _class) \
                                    else _data
                            except Exception as e:
                                # TODO
                                #print(_data)
                                #print(_class, k, keys, args)
                                #raise e # TODO
                                ret[k] = None

                    return ret

                return decode(
                    directives = directives,
                    classes = classes
                )


class api:
    class types:
        class social:
            class uid(types.string):
                pass

            class tag(types.string):
                pass

            class category(types.json.object):
                def __new__(cls, data, directives):
                    return super().__new__(cls,
                        data = data,
                        directives = directives,
                        classes = {
                            'id': types.custom(
                                default = api.types.social.uid
                            ),
                            'title': types.string
                        }
                    )

            class video(types.json.object):
                def __new__(cls, data, directives):
                    return super().__new__(cls,
                        data = data,
                        directives = directives,
                        classes = {
                            'quality': types.video.formats
                        }
                    )

            class creator(types.json.object):
                def __new__(cls, data, directives):
                    return super().__new__(cls,
                        data = data,
                        directives = directives,
                        classes = {
                            'id': types.custom(
                                default = api.types.social.uid
                            ),
                            'title': types.string,
                            'description': types.string,
                            'stats': {
                                'follower': types.integer,
                                'following': types.integer,
                                'like': types.integer,
                                'view': types.integer,
                                'post': types.integer
                            },
                            'time': types.time.absolute
                        }
                    )

            class post(types.json.object):
                def __new__(cls, data, directives):
                    return super().__new__(cls,
                        data = data,
                        directives = directives,
                        classes = {
                            'id': types.custom(
                                default = api.types.social.uid
                            ),
                            'title': types.string,
                            'description': types.string,
                            'stats': {
                                'like': types.integer,
                                'dislike': types.integer,
                                'comment': types.integer,
                                'view': types.integer,
                                'share': types.integer
                            },
                            'time': types.time.absolute,
                            'length': types.time.relative,
                            'tags': types.json.array(
                                types.custom(default = api.types.social.tag)
                            ),
                            'creator': api.types.social.creator,
                            'video': api.types.social.video,
                            'category': types.custom(
                                default = api.types.social.category
                            )
                        }
                    )

    def __init__(self,
        base_url,
        modules,
        headers = None,
        query = None
    ):
        self.defaults = {
            'base_url': base_url,
            'request': {
                'params': query,
                'headers': headers
            }
        }
        self.modules = modules

    def send(self, requests):
        if self.modules == None or  \
           self.modules.get('http') == None:
            raise NotImplementedError

        for req in requests:
            req.url = http.uri.join(self.defaults['base_url'], req.url)
            req.query = ds.merge.dicts(req.query,
                            self.defaults['request']['params'])
            req.headers = ds.merge.dicts(req.headers,
                            self.defaults['request']['headers'])

        return self.modules['http'].sendall(requests)

    def get(self,
        url: str,
        type = http.dtypes.TEXT,
        query = None, headers = None
    ):
        return next(self.send([http.request(
            method = http.methods.GET,
            url = url,
            type = type,
            query = query,
            headers = headers
        )]))
