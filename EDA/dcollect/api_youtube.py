from .webapi import webapi

from .utils import ds
from .utils.log import log
from .utils.decode import formats
from .utils.http import http


class youtube(webapi):
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

    class res_kinds:
        VIDEO = 'video'
        CHANNEL = 'channel'
        PLAYLIST = 'playlist'

    def __init__(self, modules, key, query = None, headers = None):
        self.log = log(self.__class__.__name__)
        super().__init__(
            base_url = 'https://youtube.googleapis.com',
            query = ds.merge.dicts({'key': key}, query),
            headers = headers,
            modules = modules
        )

    def listing(self,
        kind,
        query,
        count = 1,
        parts = [parts.SNIPPET],
        want = None,
        each_fn = None
    ) -> dict:
        res = []

        max_count = 50

        api_url = f'youtube/v3/{kind}/'
        api_resp_type = http.dtypes.JSON
        api_type = super().types.social.post.media

        def id_handler(id):
            if isinstance(id, dict):
                return {
                    f'youtube#{youtube.res_kinds.VIDEO}':
                        lambda: id.get('videoId'),
                    f'youtube#{youtube.res_kinds.CHANNEL}':
                        lambda: id.get('channelId'),
                    f'youtube#{youtube.res_kinds.PLAYLIST}':
                        lambda: id.get('playlistId')
                }.get(id.get('kind'), lambda: None)()
            elif isinstance(id, str):
                return id
            return None

        item_handler = super().item_handler(
            item_hint = {
                'id': (youtube.parts.ID, {'handler': id_handler}),
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
                    'comment': [youtube.parts.STATS, 'commentCount'],
                    'view': [youtube.parts.STATS, 'viewCount'],
                },
                'length': (
                    [youtube.parts.details.CONTENT, 'duration'],
                    {'format': formats.time.ISO8601}
                )
            },
            item_decoders = api_type,
            item_expect = want,
            item_each_fns = [each_fn]
        )

        page_token = None
        curr_count = count
        while len(res) < count:
            try:
                resp = super().get(
                    url = api_url,
                    type = api_resp_type,
                    query = ds.merge.dicts({
                        'part': ','.join(parts or []),
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
                res += items
                item_handler.handle(items)

            page_token = resp.get('nextPageToken')
            if not page_token:
                if len(res) != count:
                    self.log.warn(f'less data returned than expected. '
                                  f'expected {count} but was {len(res)}')
                self.log.info('reached the end of listing')
                break

            curr_count = curr_count - min(curr_count, max_count)

        return res

    def trending(self,
        count = 1,
        parts = [
            parts.ID,
            parts.SNIPPET,
            parts.STATS,
            parts.details.CONTENT
        ],
        region = None, language = None,
        **kwargs
    ) -> dict:
        return self.listing(
            kind = youtube.res_types.VIDEOS,
            query = {
                'chart': 'mostPopular',
                'regionCode': region,
                'hl': language
            },
            count = count,
            parts = parts,
            **kwargs
        )

    def search(self,
        keyword,
        count = 1,
        region = None, language = None,
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
            **kwargs
        )


class youtubei(webapi):
    def __init__(self, modules, key, query = None, headers = None):
        self.log = log(self.__class__.__name__)
        super().__init__(
            base_url = 'https://www.youtube.com',
            query = query,
            headers = headers,
            modules = modules
        )

    def initial_player_response(self, id):
        '''
        try:
            resp = super().get(
                url = 'watch/',
                type = http.dtypes.TEXT,
                query = {
                    'v': id
                }
            )
        except Exception as e:
            self.log.fatal(f'fatal error {e}. cannot proceed')

        'https://www.youtube.com/watch?v=ur560pZKRfg'

        pass
        '''
        # TODO
        raise NotImplementedError
