
class methods:
    GET = 'GET'
    POST = 'POST'

class dtypes:
    RAW = 0
    STREAM = 1
    TEXT = 2
    JSON = 3

class uri:
    from urllib.parse import urljoin
    @staticmethod
    def join(base, url):
        return uri.urljoin(base = base, url = url)

class request:
    def __init__(self,
        method,
        url,
        query = None,
        type = dtypes.TEXT,
        headers = None
    ):
        self.method = method
        self.url = url
        self.query = query
        self.type = type
        self.headers = headers

class dispatch:
    def __init__(self, conf = None):
        raise NotImplementedError

    def sendall(self, requests):
        raise NotImplementedError

    def send(self, *args, **kwargs):
        return self.sendall([request(*args, **kwargs)])
