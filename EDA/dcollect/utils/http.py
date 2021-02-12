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
