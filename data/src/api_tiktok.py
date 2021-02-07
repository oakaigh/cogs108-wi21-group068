from utils import log, formats
from webapi import webapi, http


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
        item_decode = True,
        item_each_fn = None
    ) -> dict:
        max_count = 35
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
        }
        item_decoders = super().types.social.post.media
        item_handlers = [item_each_fn]

        res = []

        first = True
        real_count = int()
        while len(res) < count:
            real_count = min(count, max_count)

            try:
                resp = super().get(
                    url = 'api/item_list',
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
                res += items
                for h in item_handlers:
                    if h:
                        for item in items:
                            item_each_fn(
                                item if not item_decode
                                else webapi.handle(
                                    item = item,
                                    hint = item_hint,
                                    decoders = item_decoders
                                )
                            )

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

        return res[:count]
