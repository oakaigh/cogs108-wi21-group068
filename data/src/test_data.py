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

logger = log('test')

def tiktok_test():
    def item_each_fn(item):
        logger.dump({
            'id': item.get('id'),
            'time_published': decode.time(item.get('createTime')),
            'stats': select.fromdict(
                o = item.get('stats'),
                renamed_keys = {
                    'commentCount': 'comment',
                    'diggCount': 'like',
                    'playCount': 'view'
                },
                encoder = decode.integer
            ),
            'duration': decode.timedelta(item.get('video', {}).get('duration'))
        })

    test_tiktok = tiktok(
        modules = modules,
        headers = conf.get('headers')
    ).trending(
        count = 1,
        item_each_fn = item_each_fn
    )

    logger.dump(test_tiktok)




def youtube_test():
    def item_each_fn(item):
        logger.dump({
            'id': item.get(youtube.parts.ID),
            'time_published': decode.time(
                    item.get(youtube.parts.SNIPPET, {}).get('publishedAt'),
                    format = decode.formats.time.ISO8601
                ),
            'stats': select.fromdict(
                o = item.get(youtube.parts.STATS),
                renamed_keys = {
                    'commentCount': 'comment',
                    'likeCount': 'like',
                    'viewCount': 'view'
                },
                encoder = decode.integer
            ),
            'duration': decode.time(
                    item.get(youtube.parts.details.CONTENT, {}).get('duration'),
                    format = decode.formats.time.ISO8601
                )
        })

    test_youtube = youtube(
        modules = modules,
        key = 'AIzaSyBKsF33Y1McGDdBWemcfcTbVyJu23XDNIk',
        headers = conf.get('headers')
    ).trending(
        count = 1,
        parts = [
            youtube.parts.ID,
            youtube.parts.SNIPPET,
            youtube.parts.STATS,
            youtube.parts.details.CONTENT
        ],
        item_each_fn = item_each_fn
    )

    logger.dump(test_youtube)


log.enable(level = log.levels.DEBUG)

thread.start([
    threading.Thread(target = tiktok_test),
    threading.Thread(target = youtube_test)
])
thread.join()
