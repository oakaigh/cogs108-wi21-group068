from .utils import http


class fasthttp(http.dispatch):
    import concurrent
    import requests_futures.sessions

    def __init__(self, conf = None):
        self.session = self.requests_futures.sessions.FuturesSession()

    def sendall(self, requests):
        fs = []

        for req in requests:
            future = self.session.request(
                method = req.method,
                url = req.url,
                params = req.query,
                headers = req.headers
            )
            future._req_dtype = req.type
            fs.append(future)

        for future in self.concurrent.futures.as_completed(fs):
            resp = future.result()
            yield {
                http.dtypes.RAW: lambda: resp,
                http.dtypes.STREAM: lambda: resp.content,
                http.dtypes.TEXT: lambda: resp.text,
                http.dtypes.JSON: lambda: resp.json()
            }.get(future._req_dtype, lambda: None)()
