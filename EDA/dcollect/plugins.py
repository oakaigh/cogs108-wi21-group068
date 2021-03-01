from .utils import http


class fasthttp(http.dispatch):
    import grequests

    def __init__(self, conf = None):
        self._ = self.grequests.Session()

    def sendall(self, requests):
        greqs = []

        for req in requests:
            greqs.append(self.grequests.request(
                method = req.method,
                url = req.url,
                params = req.query,
                headers = req.headers,
                session = self._
            ))

        resps = self.grequests.imap(greqs)
        for req, resp in zip(requests, resps):
            yield {
                http.dtypes.RAW: lambda: resp,
                http.dtypes.STREAM: lambda: resp.content,
                http.dtypes.TEXT: lambda: resp.text,
                http.dtypes.JSON: lambda: resp.json()
            }.get(req.type, lambda: None)()
