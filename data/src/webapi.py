from utils import merge
from urllib.parse import urljoin
import datetime, dateutil.parser

class http:
    class types:
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

    def get(self, url, query = None, type = types.TEXT, headers = None):
        raise NotImplementedError

class webapi:
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
        url,
        type = http.types.TEXT,
        query = None, headers = None
    ):
        if self.modules == None or  \
           self.modules.get('http') == None:
            raise NotImplementedError

        return self.modules['http'].get(
            url = http.uri.join(self.defaults['base_url'], url),
            query = merge.dicts(query,
                        self.defaults['request']['params']),
            headers = merge.dicts(headers,
                        self.defaults['request']['headers']),
            type = type
        )
