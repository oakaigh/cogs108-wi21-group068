from .utils import ds
from .utils.log import log
from .utils import http

from . import restful

class resource:
    class ad:
        class kinds:
            START = 'AD_PLACEMENT_KIND_START'
            END = 'AD_PLACEMENT_KIND_END'
            MSEC = 'AD_PLACEMENT_KIND_MILLISECONDS'
            CMD = 'AD_PLACEMENT_KIND_COMMAND_TRIGGERED'

class types:
    class ad(restful.types.json.object):
        def __new__(cls, data, directives):
            return super().__new__(cls,
                data = data,
                directives = directives,
                classes = {
                    'id': restful.types.string,
                    'kind': restful.types.string,
                    'offset': {
                        'start': restful.types.time.relative,
                        'end': restful.types.time.relative
                    }
                }
            )

class api(restful.api):
    import quickjs
    import lxml.html

    def __init__(self, modules, query = None, headers = None):
        super().__init__(
            base_url = 'https://www.youtube.com',
            query = query,
            headers = headers,
            modules = modules
        )

        self.log = log(self.__class__.__name__)

        self.ad = self.ad(self)

    def initial_player_response(self, id) -> dict:
        o_name = 'ytInitialPlayerResponse'

        id = id if not isinstance(id, str) and ds.isiter(id) else [id]

        reqs = []

        for i in id:
            try:
                reqs.append(
                    http.request(
                        method = http.methods.GET,
                        url = 'watch/',
                        type = http.dtypes.TEXT,
                        query = {'v': i}
                    )
                )
            except Exception as e:
                self.log.fatal(f'fatal error {e}. cannot proceed')

        resps = super().send(reqs)

        for resp in resps:
            root = self.lxml.html.document_fromstring(resp)
            scripts = root.xpath(
                f'.//script[contains(text(),"var {o_name}")]'
            )

            if len(scripts) > 0:
                try:
                    yield self.quickjs.Function("f",
                        """
                        function f() {
                            try {%s;} catch (e) {;}
                            return %s;
                        }
                        """ % (scripts[0].text_content(), o_name)
                    )()
                except:
                    pass

    class ad:
        def __init__(self, main):
            self.main = main

        def placements(self, id, want = None, on_result = None) -> dict:
            ret = []
            res = [] if on_result else None

            resps = self.main.initial_player_response(id = id)
            if resps is None:
                return None

            dutils = restful.utils.directives

            path_ad_base = ['adPlacementRenderer']
            path_ad_conf = path_ad_base + [
                'config', 'adPlacementConfig'
            ]

            item_type = types.ad
            item_directives = dutils.reduce(
                directives = {
                    'kind': path_ad_conf + ['kind'],
                    'offset': {
                        'start': (
                            path_ad_conf + [
                                'adTimeOffset',
                                'offsetStartMilliseconds'
                            ],
                            {'format': restful.types.time.formats.UNIX}
                        ),
                        'end': (
                            path_ad_conf + [
                                'adTimeOffset',
                                'offsetEndMilliseconds'
                            ],
                            {'format': restful.types.time.formats.UNIX}
                        )
                    }
                },
                want = want
            )
            array_type = restful.types.json.array(
                dutils.compile(item_type, item_directives),
                iterator = False
            )

            for resp in resps:
                resp_id = ds.select.descend(resp, ['videoDetails', 'videoId'])
                if resp_id == None:
                    continue

                items = resp.get('adPlacements')
                ret.append({
                    'id': resp_id,
                    'ads': array_type.__call__(items)   \
                            if not ds.isnull(items) else None
                })
                if not res == None and not items == None:
                    res += items

            if on_result:
                on_result(res)

            return ret
