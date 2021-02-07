from webapi import http
import requests


class fasthttp(http):
    def __init__(self, conf = None):
        self._ = requests.Session()

    def get(self, url, type = http.dtypes.TEXT, query = None, headers = None):
        res = self._.get(url = url, params = query, headers = headers)
        if not res:
            raise NotImplementedError

        return {
            http.dtypes.RAW: lambda: res,
            http.dtypes.STREAM: lambda: res.content,
            http.dtypes.TEXT: lambda: res.text,
            http.dtypes.JSON: lambda: res.json()
        }.get(type, lambda: None)()
