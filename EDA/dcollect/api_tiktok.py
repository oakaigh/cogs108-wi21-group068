from .utils import ds
from .utils.log import log
from .utils import http
from . import restful


types = restful.api.types.social

class kinds:
    TRENDING = 12

class filters:
    class tag:
        def __new__(cls, data):
            if isinstance(data, dict):
                return data.get('hashtagName')
            return None

class api(restful.api):
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
        item_type, # TODO isinstance(restful.types.json.object)
        item_directives,
        item_expect,

        kind,
        count,

        query,
        on_result = None
    ):
        res = [] if on_result else None

        max_count = 35

        api_url = 'api/item_list/'
        api_resp_type = http.dtypes.JSON

        dutils = restful.utils.directives
        item_directives = dutils.reduce(item_directives, item_expect)
        array_type = restful.types.json.array(
            dutils.compile(item_type, item_directives),
            iterator = True
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
                yield from array_type.__call__(items)
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
            want = None,
            **kwargs
        ) -> dict:
            return self.main.listing(
                item_type = types.post,
                item_directives = {
                    'id': 'id',
                    'description': 'desc',
                    'creator': (
                        None, {
                            'directives': {
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
                        }
                    ),
                    'stats': {
                        'like': ['stats', 'diggCount'],
                        'comment': ['stats', 'commentCount'],
                        'view': ['stats', 'playCount'],
                        'share': ['stats', 'shareCount']
                    },
                    'time': (
                        'createTime',
                        {'format': restful.types.time.formats.UNIX}
                    ),
                    'length': (
                        ['video', 'duration'],
                        {'format': restful.types.time.formats.UNIX}
                    ),
                    'tags': (
                        'textExtra', {'t': filters.tag}
                    ),
                    'video': (
                        None, {
                            'directives': {
                                'quality': ['video', 'ratio']
                            }
                        }
                    )
                },
                item_expect = want,
                kind = kinds.TRENDING,
                query = {
                    'region': region,
                    'priority_region': region,
                    'language': language
                },
                count = count,
                **kwargs
            )
