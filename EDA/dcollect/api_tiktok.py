from .webapi import webapi

from .utils.log import log
from .utils.decode import formats
from .utils import http


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
        region = None, language = None,
        want = None,
        on_result = None
    ) -> dict:
        res = [] if on_result else None

        api_type = super().types.social.post.media
        item_handler = super().item_handler(
            item_hint = {
                'id': 'id',
                'stats': {
                    'like': ['stats', 'diggCount'],
                    'comment': ['stats', 'commentCount'],
                    'view': ['stats', 'playCount'],
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
            item_decoders = api_type,
            item_expect = want
        )

        max_count = 35

        first = True
        real_count = int()
        while len(res) < count:
            real_count = min(count, max_count)

            try:
                resp = super().get(
                    url = 'api/item_list/',
                    type = http.dtypes.JSON,
                    query = {
                        'appId': 1233,
                        'id': 1,
                        'secUid': '',
                        'sourceType': 12,
                        'count': real_count,
                        'maxCursor': max_cursor,
                        'minCursor': min_cursor,
                        'region': region,
                        'priority_region': region,
                        'language': language
                    }
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
                yield from item_handler.handle(items)
                if not res == None:
                    res += items

            if not resp.get('hasMore') and not first:
                self.log.warn(f'less data returned than expected. '
                              f'expected {count} but was {len(res)}')
                break

            real_count = count - len(res)
            max_cursor = resp.get('maxCursor')
            if max_cursor == None:
                self.log.err('missing key: maxCursor')
                self.log.dump(resp)
                break

            first = False

        if on_result:
            on_result(res[:count])
