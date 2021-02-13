from .webapi import webapi

from .utils import ds
from .utils.log import log
from .utils.decode import formats
from .utils.http import http


class youtubei(webapi):
    import quickjs
    import lxml.html

    class types:
        class youtubei:
            ad = {
                'kind': None,
                'duration': None,
                'offset': {
                    'start': None,
                    'end': None
                }
            }

    def __init__(self, modules, query = None, headers = None):
        self.log = log(self.__class__.__name__)
        super().__init__(
            base_url = 'https://www.youtube.com',
            query = query,
            headers = headers,
            modules = modules
        )

    def initial_player_response(self, id) -> dict:
        o_name = 'ytInitialPlayerResponse'

        try:
            resp = super().get(
                url = 'watch/',
                type = http.dtypes.TEXT,
                query = {'v': id}
            )
        except Exception as e:
            self.log.fatal(f'fatal error {e}. cannot proceed')

        res = None
        root = self.lxml.html.document_fromstring(resp)
        scripts = root.xpath(
            f'.//script[contains(text(),"var {o_name}")]'
        )

        if len(scripts) > 0:
            try:
                res = self.quickjs.Function("f",
                    """
                    function f() {
                        try { %s; } catch (e) {;}
                        return %s;
                    }
                    """ % (scripts[0].text_content(), o_name)
                )()
            except:
                pass

        return res
