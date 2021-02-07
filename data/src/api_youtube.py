from utils import log, formats
from webapi import webapi, http


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
        parts = [
            parts.ID,
            parts.SNIPPET,
            parts.STATS,
            parts.details.CONTENT
        ],
        region = None, language = None,
        item_decode = True,
        item_each_fn = None
    ) -> dict:
        max_count = 50
        item_hint = {
            'id': youtube.parts.ID,
            'stats': {
                'like': [youtube.parts.STATS, 'likeCount'],
                'comment': [youtube.parts.STATS, 'commentCount'],
                'view': [youtube.parts.STATS, 'viewCount'],
            },
            'time': (
                [youtube.parts.SNIPPET, 'publishedAt'],
                {'format': formats.time.ISO8601}
            ),
            'length': (
                [youtube.parts.details.CONTENT, 'duration'],
                {'format': formats.time.ISO8601}
            )
        }
        item_decoders = super().types.social.post.media
        item_handlers = [item_each_fn]

        res = []

        page_token = None
        curr_count = count
        while len(res) < count:
            try:
                resp = super().get(
                    url = 'youtube/v3/videos',
                    type = http.dtypes.JSON,
                    query = {
                        'part': ','.join(parts or []),
                        'chart': 'mostPopular',
                        'maxResults': curr_count,
                        'pageToken': page_token,
                        'regionCode': region,
                        'hl': language
                    }
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
                for h in item_handlers:
                    if h:
                        for item in items:
                            print(item_hint)
                            item_each_fn(
                                item if not item_decode
                                else webapi.handle(
                                    item = item,
                                    hint = item_hint,
                                    decoders = item_decoders
                                )
                            )

            page_token = resp.get('nextPageToken')
            if not page_token:
                if len(res) != count:
                    self.log.warn(f'less data returned than expected. '
                                  f'expected {count} but was {len(res)}')
                self.log.info('reached the end of listing')
                break

            curr_count = curr_count - min(curr_count, max_count)

        return res
