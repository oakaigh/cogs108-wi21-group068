from .utils.log import log
from .utils import ds, http
from . import cache, restful
from .utils import asyncish


class resource:
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

    class kinds:
        VIDEO = 'video'
        CHANNEL = 'channel'
        PLAYLIST = 'playlist'

    class loc:
        VIDEOS = 'videos'
        CATEGORIES = 'videoCategories'
        SEARCH = 'search'
        CHANNELS = 'channels'

    class chart:
        NONE = None
        POPULAR = 'mostPopular'

    class order:
        DATE = 'date'
        RATING = 'rating'
        RELEVANCE = 'relevance'
        TITLE = 'title'
        VIDEO_COUNT = 'videoCount'
        VIEW_COUNT = 'viewCount'

    class safesearch:
        DEFAULT = None
        NONE = 'none'

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
    _api_obj = None

    @staticmethod
    def _register_api_obj(obj):
        if ds.isnull(types._api_obj):
            types._api_obj = obj

    class uid(restful.types.string):
        def __new__(cls, data):
            if isinstance(data, dict):
                return data.get({
                        f'youtube#{resource.kinds.VIDEO}': 'videoId',
                        f'youtube#{resource.kinds.CHANNEL}': 'channelId',
                        f'youtube#{resource.kinds.PLAYLIST}': 'playlistId'
                    }.get(data.get('kind'))
                )
            elif isinstance(data, str):
                return data
            return None

    class params(restful.types.string):
        def __new__(cls, data):
            return ','.join(data) if not ds.isnull(data) else None

    @cache.enable_db(
        load = lambda cl, data: cl.all.update(data or {}),
        save = lambda cl: cl.all,
        uid = 'b41d9eeb09c1'
    )
    class topic:
        all = {}
        default = 'Invalid'

        def __init__(self,
            data : str,
            region = restful.types.region.US
        ):
            if not ds.isnull(types._api_obj) and \
               ds.isnull(types.topic.all.get(region)):
                cats = types.topic.all[region] = {}
                for item in types._api_obj.categories(
                    want = {
                        'id': None,
                        'title': None
                    },
                    region = region
                ):
                    cats[item.get('id')] = item.get('title')

            self.id = str(data)

        def describe(self,
            region = restful.types.region.US
        ):
            return self.all.get(region, {}).get(str(self.id), self.default)

        # `dict` yeeted, optimization needed
        def cid(self,
            region = restful.types.region.US
        ):
            for _cid, _desc in  \
                    self.all.get(region, {}).items():
                if _cid == self.id:
                    return _cid
            return None

        def __str__(self,
            region = restful.types.region.US
        ):
            return self.describe(region = region)

        def __repr__(self,
            region = restful.types.region.US
        ):
            return f"youtube.topic.all.{region}['{self.__str__(region = region)}']"

        def __eq__(self, other):
            if type(self) == type(other):
                return str(self.id) == str(other.id)

            if isinstance(other, str):
                for region in (
                    self.all.keys() if self.all else {}
                ):
                    if self.describe(region = region) == other:
                        return True

            return False

        def __ne__(self, other):
            return not self.__eq__(str(other.id))

        def __ge__(self, other):
            return str(self.id).__ge__(str(other.id))

        def __gt__(self, other):
            return str(self.id).__gt__(str(other.id))

        def __le__(self, other):
            return str(self.id).__le__(str(other.id))

        def __lt__(self, other):
            return str(self.id).__lt__(str(other.id))

        def __hash__(self):
            return str(self.id).__hash__()

class api(restful.api):
    def __init__(self,
        modules, key,
        experiment = False,
        query = None, headers = None
    ):
        base_url = None
        base_headers = {}

        if not experiment:
            base_url = 'https://youtube.googleapis.com'
        else:
            base_url = 'https://content-youtube.googleapis.com'
            base_headers = {
                'authority': 'content-youtube.googleapis.com',
                'x-origin': 'https://explorer.apis.google.com',
                'x-referer': 'https://explorer.apis.google.com',
                'accept': '*/*',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty'
            }

        super().__init__(
            base_url = base_url,
            query = ds.merge.dicts({'key': key}, query),
            headers = ds.merge.dicts(base_headers, headers),
            modules = modules
        )

        self.log = log(self.__class__.__name__)

        self.video = self.video(self)
        self.channel = self.channel(self)

        types._register_api_obj(self)

    def listing(self,
        item_type,
        item_directives,
        item_expect,

        loc,
        count,
        parts,

        query,
        on_result = None
    ) -> dict:
        ret = []
        res = [] if on_result else None

        max_count = 50

        api_url = f'youtube/v3/{loc}/'
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
            iterator = False
        )

        res_count = 0

        page_token = None
        curr_count = count
        while ds.isnull(count) or res_count < count:
            try:
                resp = super().get(
                    url = api_url,
                    type = api_resp_type,
                    query = ds.merge.dicts({
                        'maxResults': curr_count,
                        'pageToken': page_token
                    }, query, query_default)
                )
            except Exception as e:
                self.log.fatal(f'fatal error {e}. cannot proceed')

            if ds.isnull(resp):
                self.log.warn(f'invalid response from {api_url}')
                return None

            items = resp.get('items')
            if not items:
                self.log.warn(f"{resp.get('error', '?')}: "
                              f"{resp.get('message', '?')}")
                self.log.dump(resp)
            elif not isinstance(items, list):
                self.log.warn('invalid entry')
            else:
                res_count += len(items)
                ret += array_type.__call__(items)
                if not ds.isnull(res):
                    res += items

            page_token = resp.get('nextPageToken')
            if not page_token:
                if not ds.isnull(count):
                    if res_count != count:
                        self.log.warn(f'less data returned than expected. '
                                    f'expected {count} but was {res_count}')
                self.log.info('reached the end of listing')
                break

            if not ds.isnull(curr_count):
                curr_count -= min(curr_count, max_count)

        if on_result:
            on_result(res)

        return ret

    def categories(self,
        want = None,
        region = restful.types.region.US, language = None,
        **kwargs
    ):
        return self.listing(
            item_type = types.category,
            item_directives = {
                'id': resource.parts.ID,
                'title': [resource.parts.SNIPPET, 'title']
            },
            item_expect = want,
            loc = resource.loc.CATEGORIES,
            count = None,
            parts = [resource.parts.SNIPPET],
            query = {
                'regionCode': region,
                'hl': language
            },
            **kwargs
        )

    class video:
        def __init__(self, main):
            self.main = main

        def listing(self,
            want = None,
            parts = None,
            **kwargs
        ):
            return self.main.listing(
                item_type = types.post,
                item_directives = {
                    'id': (resource.parts.ID, {'t': types.uid}),
                    'title': [resource.parts.SNIPPET, 'title'],
                    'description': [resource.parts.SNIPPET, 'description'],
                    'creator': (
                        resource.parts.SNIPPET,
                        {'directives': {'id': 'channelId'}}
                    ),
                    'time': (
                        [resource.parts.SNIPPET, 'publishedAt'],
                        {'format': restful.types.time.formats.ISO8601}
                    ),
                    'stats': {
                        'like': [resource.parts.STATS, 'likeCount'],
                        'dislike': [resource.parts.STATS, 'dislikeCount'],
                        'comment': [resource.parts.STATS, 'commentCount'],
                        'view': [resource.parts.STATS, 'viewCount'],
                    },
                    'length': (
                        [resource.parts.details.CONTENT, 'duration'],
                        {'format': restful.types.time.formats.ISO8601}
                    ),
                    'tags': [resource.parts.SNIPPET, 'tags'],
                    'video': (
                        resource.parts.details.CONTENT,
                        {'directives': {'quality': 'definition'}}
                    ),
                    'category': (
                        [resource.parts.SNIPPET, 'categoryId'],
                        {'t': types.topic}
                    )
                },
                item_expect = want,
                parts = parts,
                **kwargs
            )

        def all(self,
            count,
            id = None,
            chart = resource.chart.NONE,
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
                loc = resource.loc.VIDEOS,
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
                chart = resource.chart.POPULAR,
                region = region,
                language = language,
                count = count,
                **kwargs
            )

        def info(self, id, **kwargs):
            if ds.isnull(id):
                return None

            max_count = 50
            tasks = []

            #loop = asyncish.asyncio.new_event_loop()
            loop = asyncish.default_loop()

            for _id in ds.chunk(
                iterable = set(id if ds.isiter(id) else [id]),
                size = max_count
            ):
                tasks.append(
                    asyncish.async_wraps(
                        lambda: self.all(
                            id = _id,
                            chart = resource.chart.NONE,
                            count = len(_id),
                            **kwargs
                        )
                    )(loop = loop)
                )

            done, _ = loop.run_until_complete(
                asyncish.asyncio.wait(tasks, loop = loop)
            )
            #loop.close()

            ret = []
            for fut in done:
                ret += fut.result()

            return ret

        def search(self,
            keyword,
            count = 1,
            order = None,
            safesearch = resource.safesearch.DEFAULT,
            published_before = None, published_after = None,
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
                loc = resource.loc.SEARCH,
                query = {
                    'q': keyword,
                    'regionCode': region,
                    'relevanceLanguage': language,
                    'order': order,
                    'type': resource.kinds.VIDEO,
                    'safeSearch': safesearch,
                    'publishedBefore':
                        restful.types.time.absolute.dumps(
                            data = published_before,
                            format = restful.types.time.formats.ISO8601
                        ),
                    'publishedAfter':
                        restful.types.time.absolute.dumps(
                            data = published_after,
                            format = restful.types.time.formats.ISO8601
                        ),
                },
                count = count,
                parts = [resource.parts.SNIPPET],
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
                    'id': (resource.parts.ID, {'t': types.uid}),
                    'title': [resource.parts.SNIPPET, 'title'],
                    'description': [resource.parts.SNIPPET, 'description'],
                    'time': (
                        [resource.parts.SNIPPET, 'publishedAt'],
                        {'format': restful.types.time.formats.ISO8601}
                    ),
                    'stats': {
                        'follower': [resource.parts.STATS, 'subscriberCount'],
                        'view': [resource.parts.STATS, 'viewCount'],
                        'post': [resource.parts.STATS, 'videoCount']
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
                loc = resource.loc.CHANNELS,
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
            if ds.isnull(id):
                return None

            max_count = 50
            tasks = []

            #loop = asyncish.asyncio.new_event_loop()
            loop = asyncish.default_loop()

            for _id in ds.chunk(
                iterable = set(id if ds.isiter(id) else [id]),
                size = max_count
            ):
                tasks.append(
                    asyncish.async_wraps(
                        lambda: self.all(
                            id = _id,
                            count = len(_id),
                            **kwargs
                        )
                    )(loop = loop)
                )

            done, _ = loop.run_until_complete(
                asyncish.asyncio.wait(tasks, loop = loop)
            )
            #loop.close()

            ret = []
            for fut in done:
                ret += fut.result()

            return ret
