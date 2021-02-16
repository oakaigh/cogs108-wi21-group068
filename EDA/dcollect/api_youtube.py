from .webapi import webapi

from .utils import ds
from .utils.log import log
from .utils.decode import formats
from .utils import http


class youtube(webapi):
    types = webapi.types.social.post

    class parts:
        class details:
            CONTENT = 'contentDetails'
            FILE = 'fileDetails'
            LIVE = 'liveStreamingDetails'
            PROC = 'processingDetails'
            REC = 'recordingDetails'
            TOPIC = 'topicDetails'
        ID = 'id'
        LOCAL = 'localizations'
        PLAYER = 'player'
        SNIPPET = 'snippet'
        STATS = 'statistics'
        STATUS = 'status'
        SUGGEST = 'suggestions'

    class res_types:
        VIDEOS = 'videos'
        SEARCH = 'search'
        CHANNELS = 'channels'

    class res_kinds:
        VIDEO = 'video'
        CHANNEL = 'channel'
        PLAYLIST = 'playlist'

    class utils:
        @staticmethod
        def multiparam(vars):
            return ','.join(vars or [])

        @staticmethod
        def parse_id(id):
            if isinstance(id, dict):
                return id.get({
                        f'youtube#{youtube.res_kinds.VIDEO}': 'videoId',
                        f'youtube#{youtube.res_kinds.CHANNEL}': 'channelId',
                        f'youtube#{youtube.res_kinds.PLAYLIST}': 'playlistId'
                    }.get(id.get('kind'))
                )
            elif isinstance(id, str):
                return id
            return None

        @staticmethod
        def hint_parts(hint: dict):
            parts = set()

            for k, keys, args in    \
                webapi.decoder.hint_traversal(hint = hint):
                if len(keys) == 0:
                    continue
                parts.add(keys[0])

            return parts

    def __init__(self, modules, key, query = None, headers = None):
        super().__init__(
            base_url = 'https://youtube.googleapis.com',
            query = ds.merge.dicts({'key': key}, query),
            headers = headers,
            modules = modules
        )

        self.log = log(self.__class__.__name__)

        self.video = self.video(self)
        self.channel = self.channel(self)

    def listing(self,
        kind,
        api_type,
        item_hint,
        query,
        count,
        parts = None,
        want = None,
        on_result = None
    ) -> dict:
        res = [] if on_result else None

        max_count = 50

        api_url = f'youtube/v3/{kind}/'
        api_resp_type = http.dtypes.JSON

        item_handler = self.item_handler(
            item_hint = item_hint,
            item_decoders = api_type,
            item_expect = want
        )

        if parts == None:
            parts = youtube.utils.hint_parts(
                        item_handler.item_hint
                    )
        part_qstr = self.utils.multiparam(parts)

        res_count = 0

        page_token = None
        curr_count = count
        while res_count < count:
            try:
                resp = self.get(
                    url = api_url,
                    type = api_resp_type,
                    query = ds.merge.dicts({
                        'part': part_qstr,
                        'maxResults': curr_count,
                        'pageToken': page_token
                    }, query)
                )
            except Exception as e:
                self.log.fatal(f'fatal error {e}. cannot proceed')

            items = resp.get('items')
            if not items:
                self.log.warn(f"{resp.get('error', '?')}: "
                              f"{resp.get('message', '?')}")
                self.log.dump(resp)
            elif not isinstance(items, list):
                self.log.warn('invalid entry')
            else:
                res_count += len(items)
                yield from item_handler.handle(items)
                if not res == None:
                    res += items

            page_token = resp.get('nextPageToken')
            if not page_token:
                if res_count != count:
                    self.log.warn(f'less data returned than expected. '
                                  f'expected {count} but was {res_count}')
                self.log.info('reached the end of listing')
                break

            curr_count = curr_count - min(curr_count, max_count)

        if on_result:
            on_result(res)

    class video:
        class chart:
            NONE = None
            POPULAR = 'mostPopular'

        def __init__(self, main):
            self.main = main

        def listing(self, **kwargs):
            return self.main.listing(
                api_type = self.main.types.media,
                item_hint = {
                    'id': (
                        youtube.parts.ID,
                        {'handler': self.main.utils.parse_id}
                    ),
                    'title': [youtube.parts.SNIPPET, 'title'],
                    'description': [youtube.parts.SNIPPET, 'description'],
                    'creator': {
                        'id': [youtube.parts.SNIPPET, 'channelId']
                    },
                    'time': (
                        [youtube.parts.SNIPPET, 'publishedAt'],
                        {'format': formats.time.ISO8601}
                    ),
                    'stats': {
                        'like': [youtube.parts.STATS, 'likeCount'],
                        'dislike': [youtube.parts.STATS, 'dislikeCount'],
                        'comment': [youtube.parts.STATS, 'commentCount'],
                        'view': [youtube.parts.STATS, 'viewCount'],
                    },
                    'length': (
                        [youtube.parts.details.CONTENT, 'duration'],
                        {'format': formats.time.ISO8601}
                    )
                },
                **kwargs
            )

        def all(self,
            count,
            id = None,
            chart = chart.NONE,
            region = None, language = None,
            want = {
                'id':  None,
                'title': None,
                'description': None,
                'creator': {'id': None},
                'time': None,
                'stats': {
                    'like': None,
                    'comment': None,
                    'view': None,
                },
                'length': None
            },
            **kwargs
        ):
            return self.listing(
                kind = youtube.res_types.VIDEOS,
                query = {
                    'chart': chart,
                    'id': self.main.utils.multiparam(id) if id else None,
                    'regionCode': region,
                    'hl': language
                },
                count = count,
                **kwargs
            )

        def trending(self,
            count = 1,
            region = None, language = None,
            **kwargs
        ) -> dict:
            return self.all(
                chart = self.chart.POPULAR,
                region = region,
                language = language,
                count = count,
                **kwargs
            )

        def info(self, id, **kwargs):
            if id == None:
                return None
            return self.all(
                id = id,
                chart = self.chart.NONE,
                count = len(id) if ds.isiter(id) else len([id]),
                **kwargs
            )

        def search(self,
            keyword,
            count = 1,
            region = None, language = None,
            want = {
                'id': None,
                'title': None,
                'description': None,
                'creator': {'id': None},
                'time': None
            },
            **kwargs
        ):
            return self.listing(
                kind = youtube.res_types.SEARCH,
                query = {
                    'q': keyword,
                    'regionCode': region,
                    'relevanceLanguage': language
                },
                count = count,
                parts = [youtube.parts.SNIPPET],
                want = want,
                **kwargs
            )

    class channel:
        def __init__(self, main):
            self.main = main

        def listing(self, **kwargs):
            return self.main.listing(
                api_type = self.main.types.creator,
                item_hint = {
                    'id': (
                        youtube.parts.ID,
                        {'handler': self.main.utils.parse_id}
                    ),
                    'title': [youtube.parts.SNIPPET, 'title'],
                    'description': [youtube.parts.SNIPPET, 'description'],
                    'time': (
                        [youtube.parts.SNIPPET, 'publishedAt'],
                        {'format': formats.time.ISO8601}
                    ),
                    'stats': {
                        'follower': [youtube.parts.STATS, 'subscriberCount'],
                        'view': [youtube.parts.STATS, 'viewCount'],
                        'post': [youtube.parts.STATS, 'videoCount']
                    }
                },
                **kwargs
            )

        def all(self,
            count,
            id = None,
            name = None,
            language = None,
            want = {
                'id': None,
                'title': None,
                'description': None,
                'time': None,
                'stats': {
                    'follower': None,
                    'view': None,
                    'post': None
                }
            },
            **kwargs
        ):
            return self.listing(
                kind = youtube.res_types.CHANNELS,
                query = {
                    'id': self.main.utils.multiparam(id) if id else None,
                    'forUsername': name,
                    'hl': language
                },
                count = count,
                **kwargs
            )

        def info(self, id, **kwargs):
            return self.all(
                id = id,
                count = len(id) if ds.isiter(id) else len([id]),
                **kwargs
            )
