import utils
from urllib.parse import urljoin

class http:
    class dtypes:
        RAW = 0,
        STREAM = 1,
        TEXT = 2,
        JSON = 3

    class uri:
        @staticmethod
        def join(base, url):
            return urljoin(base = base, url = url)

    def __init__(self, conf = None):
        raise NotImplementedError

    def get(self, url, query = None, type = dtypes.TEXT, headers = None):
        raise NotImplementedError

class webapi:
    class types:
        class social: # social platforms
            class post:
                media = {
                    'id': utils.dtypes.string,
                    'stats': {
                        'like': utils.dtypes.integer,
                        'comment': utils.dtypes.integer,
                        'view': utils.dtypes.integer
                    },
                    'time': utils.dtypes.time,
                    'length': utils.dtypes.duration
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

    def get(self,
        url: str,
        type = http.dtypes.TEXT,
        query = None, headers = None
    ):
        if self.modules == None or  \
           self.modules.get('http') == None:
            raise NotImplementedError

        return self.modules['http'].get(
            url = http.uri.join(self.defaults['base_url'], url),
            query = utils.merge.dicts(query,
                        self.defaults['request']['params']),
            headers = utils.merge.dicts(headers,
                        self.defaults['request']['headers']),
            type = type
        )

    class item_handler:
        def __init__(self,
            item_hint = None,
            item_decoders = None,
            item_expect = None,
            item_each_fns = None
        ):
            self.item_hint = utils.select.fromdict(
                                o = item_hint,
                                renamed_keys = item_expect
                            ) if item_expect else item_hint
            self.item_decoders = item_decoders
            self.item_each_fns = item_each_fns
            pass

        def handle(self, items):
            def decode(
                item: dict,
                hint: dict,
                decoders: dict,
                decoder_default = lambda x: x,
                inplace = False
            ) -> dict:
                ret = hint if inplace else {}
                for k, v in hint.items():
                    if isinstance(v, dict):
                        ret[k] = decode(
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

                        ret[k] = ((decoders and decoders.get(k)) or decoder_default)(
                            utils.select.descend(
                                o = item,
                                keys = keys if isinstance(keys, list) else [keys]
                            ),
                            **(args if args else {})
                        )
                return ret

            for f in self.item_each_fns:
                if f:
                    for item in items:
                        f(
                            decode(
                                item = item,
                                hint = self.item_hint,
                                decoders = self.item_decoders
                            ) if self.item_hint and self.item_decoders
                            else item
                        )
