from .utils import ds
from .utils.log import log
from .utils import http
from . import restful


class res_parts:
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
    CATEGORIES = 'videoCategories'
    SEARCH = 'search'
    CHANNELS = 'channels'

class res_kinds:
    VIDEO = 'video'
    CHANNEL = 'channel'
    PLAYLIST = 'playlist'

class utils:
    @staticmethod
    def hint_parts(hint: dict):
        parts = set()

        for k, keys, args, filter_fn in    \
            restful.utils.directives.traversal(hint):
            if not keys:
                continue
            parts.add(keys[0])

        return parts

class types(restful.api.types.social):
    class uid(restful.types.string):
        def __new__(cls, data):
            if isinstance(data, dict):
                return data.get({
                        f'youtube#{res_kinds.VIDEO}': 'videoId',
                        f'youtube#{res_kinds.CHANNEL}': 'channelId',
                        f'youtube#{res_kinds.PLAYLIST}': 'playlistId'
                    }.get(data.get('kind'))
                )
            elif isinstance(data, str):
                return data
            return None

    class params(restful.types.string):
        def __new__(cls, data):
            return ','.join(data) if not ds.isnull(data) else None

class api(restful.api):
    def __init__(self,
        modules, key,
        query = None, headers = None
    ):
        super().__init__(
            base_url = 'https://youtube.googleapis.com',
            query = ds.merge.dicts({'key': key}, query),
            headers = headers,
            modules = modules
        )

        self.log = log(self.__class__.__name__)

        self.video = self.video(self)
        self.channel = self.channel(self)

        self.types = self.types(self)

    class types:
        def __init__(self, main):
            self.category = self._category(main)

        @staticmethod
        def _category(main):
            class _:
                all = {}

                def __init__(self,
                    data : str,
                    region = restful.types.region.US
                ):
                    if self.all.get(region) == None:
                        cats = self.all[region] = {}
                        for item in main.categories(
                            want = {
                                'id': None,
                                'title': None
                            },
                            region = region
                        ):
                            cats[item.get('id')] = item.get('title')

                    self.id = data

                def __str__(self,
                    region = restful.types.region.US
                ):
                    return self.all.get(region, {}).get(self.id)

                def __repr__(self,
                    region = restful.types.region.US
                ):
                    return f"youtube.category.all.{region}['{self.__str__(region)}']"

            return _


    def listing(self,
        item_type, # TODO isinstance(restful.types.json.object)
        item_directives,
        item_expect,

        kind,
        count,
        parts,

        query,
        on_result = None
    ) -> dict:
        res = [] if on_result else None

        max_count = 50

        api_url = f'youtube/v3/{kind}/'
        api_resp_type = http.dtypes.JSON

        dutils = restful.utils.directives
        item_directives = dutils.reduce(item_directives, item_expect)
        query_default = {
            'part': types.params(
                        parts or utils.hint_parts(item_directives)
                    )
        }
        array_type = restful.types.json.array(
            dutils.compile(item_type, item_directives),
            iterator = True
        )

        res_count = 0

        page_token = None
        curr_count = count
        while count == None or res_count < count:
            try:
                resp = self.get(
                    url = api_url,
                    type = api_resp_type,
                    query = ds.merge.dicts({
                        'maxResults': curr_count,
                        'pageToken': page_token
                    }, query, query_default)
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
                yield from array_type.__call__(items)
                if not res == None:
                    res += items

            page_token = resp.get('nextPageToken')
            if not page_token:
                if count != None and res_count != count:
                    self.log.warn(f'less data returned than expected. '
                                  f'expected {count} but was {res_count}')
                self.log.info('reached the end of listing')
                break

            curr_count = curr_count - min(curr_count, max_count)

        if on_result:
            on_result(res)

    def categories(self,
        want = None,
        region = restful.types.region.US, language = None,
        **kwargs
    ):
        return self.listing(
            item_type = types.category,
            item_directives = {
                'id': res_parts.ID,
                'title': [res_parts.SNIPPET, 'title']
            },
            item_expect = want,
            kind = res_types.CATEGORIES,
            count = None,
            parts = [res_parts.SNIPPET],
            query = {
                'regionCode': region,
                'hl': language
            },
            **kwargs
        )

    class video:
        class chart:
            NONE = None
            POPULAR = 'mostPopular'

        def __init__(self, main):
            self.main = main

        def listing(self, want = None, parts = None, **kwargs):
            return self.main.listing(
                item_type = types.post,
                item_directives = {
                    'id': (res_parts.ID, {'t': types.uid}),
                    'title': [res_parts.SNIPPET, 'title'],
                    'description': [res_parts.SNIPPET, 'description'],
                    'creator': (
                        res_parts.SNIPPET,
                        {'directives': {'id': 'channelId'}}
                    ),
                    'time': (
                        [res_parts.SNIPPET, 'publishedAt'],
                        {'format': restful.types.time.formats.ISO8601}
                    ),
                    'stats': {
                        'like': [res_parts.STATS, 'likeCount'],
                        'dislike': [res_parts.STATS, 'dislikeCount'],
                        'comment': [res_parts.STATS, 'commentCount'],
                        'view': [res_parts.STATS, 'viewCount'],
                    },
                    'length': (
                        [res_parts.details.CONTENT, 'duration'],
                        {'format': restful.types.time.formats.ISO8601}
                    ),
                    'tags': [res_parts.SNIPPET, 'tags'],
                    'video': (
                        res_parts.details.CONTENT,
                        {'directives': {'quality': 'definition'}}
                    ),
                    'category': (
                        [res_parts.SNIPPET, 'categoryId'],
                        {'t': self.main.types.category}
                    )
                },
                item_expect = want,
                parts = parts,
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
                'creator': None,
                'time': None,
                'stats': None,
                'length': None,
                'tags': None,
                'video': None,
                'category': None
            },
            **kwargs
        ):
            return self.listing(
                kind = res_types.VIDEOS,
                query = {
                    'chart': chart,
                    'id': types.params(id),
                    'regionCode': region,
                    'hl': language
                },
                count = count,
                want = want,
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
                'time': None,
                'tags': None
            },
            **kwargs
        ):
            return self.listing(
                kind = res_types.SEARCH,
                query = {
                    'q': keyword,
                    'regionCode': region,
                    'relevanceLanguage': language
                },
                count = count,
                parts = [res_parts.SNIPPET],
                want = want,
                **kwargs
            )

    class channel:
        def __init__(self, main):
            self.main = main

        def listing(self, want = None, parts = None, **kwargs):
            return self.main.listing(
                item_type = types.creator,
                item_directives = {
                    'id': (res_parts.ID, {'t': types.uid}),
                    'title': [res_parts.SNIPPET, 'title'],
                    'description': [res_parts.SNIPPET, 'description'],
                    'time': (
                        [res_parts.SNIPPET, 'publishedAt'],
                        {'format': restful.types.time.formats.ISO8601}
                    ),
                    'stats': {
                        'follower': [res_parts.STATS, 'subscriberCount'],
                        'view': [res_parts.STATS, 'viewCount'],
                        'post': [res_parts.STATS, 'videoCount']
                    }
                },
                item_expect = want,
                parts = parts,
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
                'stats': None
            },
            **kwargs
        ):
            return self.listing(
                kind = res_types.CHANNELS,
                query = {
                    'id': types.params(id),
                    'forUsername': name,
                    'hl': language
                },
                count = count,
                want = want,
                **kwargs
            )

        def info(self, id, **kwargs):
            return self.all(
                id = id,
                count = len(id) if ds.isiter(id) else len([id]),
                **kwargs
            )
