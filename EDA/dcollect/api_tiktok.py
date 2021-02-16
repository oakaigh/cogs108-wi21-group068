from .webapi import webapi

from .utils import ds
from .utils.log import log
from .utils.decode import formats
from .utils import http


class tiktok(webapi):
    types = webapi.types.social.post

    class kinds:
        TRENDING = 12

    def __init__(self, modules, query = None, headers = None):
        super().__init__(
            base_url = 'https://www.tiktok.com',
            query = query,
            headers = headers,
            modules = modules
        )

        self.log = log(self.__class__.__name__)

        self.video = self.video(self)

    '''
    TikTok Video Listing API
    Reference https://github.com/davidteather/TikTok-Api
    '''
    def listing(self,
        kind,
        api_type,
        item_hint,
        query,
        count,
        want = None,
        on_result = None
    ):
        res = [] if on_result else None

        max_count = 35

        api_url = 'api/item_list/'
        api_resp_type = http.dtypes.JSON

        item_handler = super().item_handler(
            item_hint = item_hint,
            item_decoders = api_type,
            item_expect = want
        )

        res_count = 0

        first = True
        real_count = int()
        min_cursor = 0
        max_cursor = 0
        while res_count < count:
            real_count = min(count, max_count)

            try:
                resp = super().get(
                    url = api_url,
                    type = api_resp_type,
                    query = ds.merge.dicts({
                        'appId': 1233,
                        'sourceType': kind,
                        'count': real_count,
                        'maxCursor': max_cursor,
                        'minCursor': min_cursor
                    }, query)
                )
            except Exception as e:
                self.log.fatal(f'fatal error {e}. cannot proceed')

            items = resp.get('items')
            if not items:
                self.log.warn(f"{resp.get('statusCode', '?')}: "
                              f"{resp.get('statusMsg', '?')}")
                self.log.dump(resp)
            elif not isinstance(items, list):
                self.log.warn('invalid entry')
            else:
                res_count += len(items)
                yield from item_handler.handle(items)
                if not res == None:
                    res += items

            if not resp.get('hasMore') and not first:
                self.log.warn(f'less data returned than expected. '
                              f'expected {count} but was {res_count}')
                break

            real_count = count - res_count
            max_cursor = resp.get('maxCursor')
            if max_cursor == None:
                self.log.err('missing key: maxCursor')
                self.log.dump(resp)
                break

            first = False

        if on_result:
            on_result(res[:count])

    class video:
        def __init__(self, main):
            self.main = main

        def trending(self,
            count = 1,
            region = None, language = None,
            **kwargs
        ) -> dict:
            return self.main.listing(
                kind = self.main.kinds.TRENDING,
                api_type = self.main.types.media,
                item_hint = {
                    'id': 'id',
                    'description': 'desc',
                    'creator': {
                        'id': ['author', 'id'],
                        'title': ['author', 'nickname'],
                        'description': ['author', 'signature'],
                        'stats': {
                            'follower': ['authorStats', 'followerCount'],
                            'following': ['authorStats', 'followingCount'],
                            'like': ['authorStats', 'diggCount'],
                            'view': ['authorStats', 'heartCount'],
                            'post': ['authorStats', 'videoCount']
                        }
                    },
                    'stats': {
                        'like': ['stats', 'diggCount'],
                        'comment': ['stats', 'commentCount'],
                        'view': ['stats', 'playCount'],
                        'share': ['stats', 'shareCount']
                    },
                    'time': (
                        'createTime',
                        {'format': formats.time.UNIX}
                    ),
                    'length': (
                        ['video', 'duration'],
                        {'format': formats.time.UNIX}
                    )
                },
                query = {
                    'region': region,
                    'priority_region': region,
                    'language': language
                },
                count = count,
                **kwargs
            )
