from .utils import ds
from .utils import http
from .utils.decode import dtypes


class webapi:
    class types:
        class social: # social platforms
            class post:
                media = {
                    'id': dtypes.any,
                    'title': dtypes.string,
                    'description': dtypes.string,
                    'creator': {
                        'id': dtypes.any
                    },
                    'stats': {
                        'like': dtypes.integer,
                        'comment': dtypes.integer,
                        'view': dtypes.integer
                    },
                    'time': dtypes.time,
                    'length': dtypes.duration
                }
                creator = {
                    'id': dtypes.any,
                    'title': dtypes.string,
                    'description': dtypes.string,
                    'stats': {
                        'follow': dtypes.integer,
                        'view': dtypes.integer,
                        'posts': dtypes.integer
                    },
                    'time': dtypes.time
                }

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

    class decoder:
        @staticmethod
        def hint_traversal(
            hint: dict
        ):
            for k, v in hint.items():
                if isinstance(v, dict):
                    yield from webapi.decoder.hint_traversal(v)
                else:
                    keys, args = None, None
                    if isinstance(v, tuple):
                        keys, args = v
                    else:
                        keys = v

                    if not isinstance(keys, list):
                        keys = [keys]
                    if not args:
                        args = {}

                    yield k, keys, args

        @staticmethod
        def decode(
            item: dict,
            hint: dict,
            decoders: dict,
            decoder_default = lambda x: x,
            inplace = False,
            filter = None
        ) -> dict:
            ret = hint if inplace else {}
            for k, v in hint.items():
                if isinstance(v, dict):
                    ret[k] = webapi.decoder.decode(
                        item = item,
                        hint = v,
                        decoders = decoders.get(k),
                        decoder_default = decoder_default,
                        inplace = inplace
                    )
                else:
                    keys, args = None, None
                    if isinstance(v, tuple):
                        keys, args = v
                    else:
                        keys = v

                    if not isinstance(keys, list):
                        keys = [keys]
                    if not args:
                        args = {}

                    if filter:
                        if not filter(k, keys, args):
                            continue

                    ret[k] = ((decoders and decoders.get(k)) or decoder_default)(
                        ds.select.descend(o = item, keys = keys), **args
                    )
            return ret

    class item_handler:
        def __init__(self,
            item_hint = None,
            item_decoders = None,
            item_expect = None
        ):
            self.item_hint = ds.deep_update(
                                source = item_expect,
                                overrides = item_hint,
                                inplace = False,
                                itersect = True
                            ) if item_expect else item_hint
            self.item_decoders = item_decoders

        def handle(self, items, inplace = False):
            if self.item_hint and self.item_decoders:
                for item in items:
                    yield webapi.decoder.decode(
                        item = item,
                        hint = self.item_hint,
                        decoders = self.item_decoders,
                        inplace = inplace
                    )
            else:
                yield from items
