from webapi import http
import requests


class fasthttp(http):
    def __init__(self, conf = None):
        self._ = requests.Session()

    def get(self, url, type = http.types.TEXT, query = None, headers = None):
        res = self._.get(url = url, params = query, headers = headers)
        if not res:
            raise NotImplementedError

        return {
            http.types.RAW: res,
            http.types.STREAM: res.content,
            http.types.TEXT: res.text,
            http.types.JSON: res.json()
        }.get(type)
