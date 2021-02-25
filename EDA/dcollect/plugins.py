from .utils import http
import grequests


class fasthttp(http.dispatch):
    def __init__(self, conf = None):
        self._ = grequests.Session()

    def sendall(self, requests):
        greqs = []

        for req in requests:
            greqs.append(grequests.request(
                method = req.method,
                url = req.url,
                params = req.query,
                headers = req.headers,
                session = self._
            ))

        resps = grequests.imap(greqs)
        for req, resp in zip(requests, resps):
            yield {
                http.dtypes.RAW: lambda: resp,
                http.dtypes.STREAM: lambda: resp.content,
                http.dtypes.TEXT: lambda: resp.text,
                http.dtypes.JSON: lambda: resp.json()
            }.get(req.type, lambda: None)()
