

from urllib.parse import urljoin

class http:
    class types:
        raw = 0,
        binary = 1,
        text = 2,
        json = 3

    class uri:
        @staticmethod
        def join(base, url):
            return urljoin(base = base, url = url)

    def __init__(self, conf = None):
        raise NotImplementedError

    def get(self, url, query = None, type = types.text, headers = None):
        raise NotImplementedError



import requests

class fasthttp(http):
    def __init__(self, conf = None):
        self._ = requests.Session()

    def get(self, url, type = http.types.text, query = None, headers = None):
        res = self._.get(url = url, params = query, headers = headers)

        return {
            http.types.raw: res,
            http.types.binary: res.content,
            http.types.text: res.text,
            http.types.json: res.json()
        }.get(type)




class noice:
    @staticmethod
    def merge_dictlist(dicts) -> dict:
        ret = None
        for d in dicts:
            if d:
                if not ret:
                    ret = dict()
                ret.update(d)
        return ret

    @staticmethod
    def merge_dicts(*args) -> dict:
        return noice.merge_dictlist(list(args))


class webapi:
    def __init__(self,
        base_url,
        headers = None,
        query = None,
        modules = {'http': fasthttp()}
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
        type = http.types.text,
        query = None, headers = None
    ):
        if self.modules.get('http') == None:
            raise NotImplementedError

        return self.modules['http'].get(
            url = http.uri.join(self.defaults['base_url'], url),
            query = noice.merge_dicts(query,
                        self.defaults['request']['params']),
            headers = noice.merge_dicts(headers,
                        self.defaults['request']['headers']),
            type = type
        )





import logging, sys
class log:
    def __init__(self, scope_id = None):
        self.id = scope_id

    def fmt(self, string):
        return f'[{self.id}] {string}'

    def info(self, string): return logging.info(self.fmt(string))
    def err(self, string): return logging.error(self.fmt(string))
    def warn(self, string): return logging.warning(self.fmt(string))
    def debug(self, string): return logging.debug(self.fmt(string))
    def dump(self, obj):
        self.debug('object dumped')
        self.debug(obj)

    def fatal(self, string):
        self.err(self.fmt(string))
        sys.exit(1)


class tiktok(webapi):
    def __init__(self, modules, query = None, headers = None):
        self.log = log(self.__class__.__name__)
        super().__init__(
            base_url = 'https://www.tiktok.com',
            query = query,
            headers = headers,
            modules = modules
        )

    '''
    Get TikTok trending data
    Reference https://github.com/davidteather/TikTok-Api
    '''
    def trending(self,
        count = 1,
        min_cursor = 0, max_cursor = 0,
        region = None, language = None
    ) -> dict:
        max_count = 35

        res = []

        first = True
        real_count = int()
        while len(res) < count:
            real_count = min(count, max_count)

            try:
                resp = super().get(
                    url = 'api/item_list',
                    type = http.types.json,
                    query = {
                        "appId": 1233,
                        "id": 1,
                        "secUid": "",
                        "sourceType": 12,
                        "count": real_count,
                        "maxCursor": max_cursor,
                        "minCursor": min_cursor,
                        "region": region,
                        "priority_region": region,
                        "language": language
                    }
                )
            except Exception as e:
                self.log.fatal(f'fatal error {e}. cannot proceed')

            status = resp.get('statusCode')
            if status == None or status != 0:
                self.log.warn("non-zero status code returned")
                self.log.warn(f"{status}: "
                              f"{resp.get('statusMsg', '?')}")
                self.log.dump(resp)

            res = res + resp.get("items", [])

            if not resp.get("hasMore") and not first:
                self.log.warn(f'less data returned than expected. '
                              f'expected {count} but was {len(res)}')
                break

            real_count = count - len(res)
            max_cursor = resp.get("maxCursor")
            if max_cursor == None:
                self.log.err("missing key: maxCursor")
                self.log.dump(resp)
                break

            first = False

        return res[:count]

class youtube(webapi):
    def __init__(self, modules, key, query = None, headers = None):
        self.log = log(self.__class__.__name__)
        super().__init__(
            base_url = 'https://youtube.googleapis.com',
            query = {'key': key},
            headers = headers,
            modules = modules
        )

    def trending(self,
        count = 1,
        parts = [ 'statistics', 'contentDetails', 'snippet' ]
    ) -> dict:
        max_count = 50

        res = []

        page_token = None
        curr_count = count
        while len(res) < count:
            try:
                resp = super().get(
                    url = 'youtube/v3/videos',
                    type = http.types.json,
                    query = {
                        'part': ','.join(parts or []),
                        'chart': 'mostPopular',
                        'maxResults': curr_count,
                        'pageToken': page_token
                    }
                )
            except Exception as e:
                self.log.fatal(f'fatal error {e}. cannot proceed')

            items = resp.get('items')
            if not items:
                self.log.warn(f"{resp.get('error', '?')}: "
                              f"{resp.get('message', '?')}")
                self.log.dump(resp)
            else:
                res = res + items

            page_token = resp.get('nextPageToken')
            if not page_token:
                if len(res) != count:
                    self.log.warn(f'less data returned than expected. '
                                  f'expected {count} but was {len(res)}')
                self.log.info("reached the end of listing")
                break

            curr_count = curr_count - min(curr_count, max_count)

        return res




conf = {
    'http': {
        'module': fasthttp(),
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
    }
}

modules = {
    'http': conf['http']['module']
}

import json

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

test_tiktok = tiktok(
    modules = modules,
    headers = conf.get('headers')
).trending(count = 1)

print(len(test_tiktok))
print(json.dumps(test_tiktok, indent = 4))

test_youtube = youtube(
    modules = modules,
    key = 'AIzaSyBKsF33Y1McGDdBWemcfcTbVyJu23XDNIk',
    headers = conf.get('headers')
).trending(count = 1)

print(len(test_youtube))
print(json.dumps(test_youtube, indent = 4))
