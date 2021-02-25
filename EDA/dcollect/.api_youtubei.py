from .webapi import webapi

from .utils import ds
from .utils.log import log
from .utils.decode import formats
from .utils import http
from .utils.decode import dtypes

import quickjs
import lxml.html


class youtubei(webapi):
    class types:
        class youtubei:
            ad = {
                'id': dtypes.any,
                'kind': dtypes.string,
                'offset': {
                    'start': dtypes.duration,
                    'end': dtypes.duration
                }
            }

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

        id = id if isinstance(id, list) else [id]

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
            root = lxml.html.document_fromstring(resp)
            scripts = root.xpath(
                f'.//script[contains(text(),"var {o_name}")]'
            )

            if len(scripts) > 0:
                try:
                    yield quickjs.Function("f",
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
        class kinds:
            START = 'AD_PLACEMENT_KIND_START'
            END = 'AD_PLACEMENT_KIND_END'
            MSEC = 'AD_PLACEMENT_KIND_MILLISECONDS'
            CMD = 'AD_PLACEMENT_KIND_COMMAND_TRIGGERED'

        def __init__(self, main):
            self.main = main

        def placements(self, id, want = None, on_result = None) -> dict:
            res = [] if on_result else None

            resps = self.main.initial_player_response(id = id)
            if resps is None:
                return None

            for resp in resps:
                resp_id = ds.select.descend(resp, ['videoDetails', 'videoId'])

                items = resp.get('adPlacements')
                if items is None:
                    yield None
                    continue

                path_ad_base = ['adPlacementRenderer']
                path_ad_conf = path_ad_base + [
                    'config', 'adPlacementConfig'
                ]

                item_handler = self.main.item_handler(
                    item_hint = {
                        'kind': path_ad_conf + ['kind'],
                        'offset': {
                            'start': (
                                path_ad_conf + [
                                    'adTimeOffset',
                                    'offsetStartMilliseconds'
                                ],
                                {'format': formats.time.UNIX}
                            ),
                            'end': (
                                path_ad_conf + [
                                    'adTimeOffset',
                                    'offsetEndMilliseconds'
                                ],
                                {'format': formats.time.UNIX}
                            )
                        }
                    },
                    item_decoders = self.main.types.youtubei.ad,
                    item_expect = want
                )

                yield {
                    'id': resp_id,
                    'ads': list(item_handler.handle(items))
                }
                if not res == None:
                    res += items

            if on_result:
                on_result(res)
