from utils import log, thread, decode, select

from mod_fasthttp import fasthttp
from api_tiktok import tiktok
from api_youtube import youtube

import threading


conf = {
    'http': {
        'module': fasthttp(),
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
    }
}

modules = {
    'http': conf['http']['module']
}

count = 1
log_resp = False


logger = log('test')

def tiktok_test():
    def item_each_fn(item):
        logger.dump(item)

    test_tiktok = tiktok(
        modules = modules,
        headers = conf.get('headers')
    ).trending(
        count = count,
        each_fn = item_each_fn
    )

    if log_resp: logger.dump(test_tiktok)


def youtube_test():
    def item_each_fn(item):
        logger.dump(item)

    test_youtube = youtube(
        modules = modules,
        key = 'AIzaSyBKsF33Y1McGDdBWemcfcTbVyJu23XDNIk',
        headers = conf.get('headers')
    ).trending(
        count = count,
        parts = [
            youtube.parts.ID,
            youtube.parts.SNIPPET,
            youtube.parts.STATS,
            youtube.parts.details.CONTENT
        ],
        want = {'id': None},
        each_fn = item_each_fn
    )

    if log_resp: logger.dump(test_youtube)


log.enable(level = log.levels.DEBUG)

thread.start([
    threading.Thread(target = tiktok_test),
    threading.Thread(target = youtube_test)
])
thread.join()
