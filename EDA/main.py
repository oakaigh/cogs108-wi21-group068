from dcollect import *

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

    youtube_o = youtube(
        modules = modules,
        key = 'AIzaSyBKsF33Y1McGDdBWemcfcTbVyJu23XDNIk',
        headers = conf.get('headers')
    )

    logger.info('testing: youtube trending')
    test_youtube_trending = youtube_o.trending(
        count = count,
        parts = [
            youtube.parts.ID,
            youtube.parts.SNIPPET,
            youtube.parts.STATS,
            youtube.parts.details.CONTENT
        ],
        #want = {'id': None},
        each_fn = item_each_fn
    )
    if log_resp: logger.dump(test_youtube_trending)

    logger.info('testing: youtube search')
    test_youtube_search = youtube_o.search(
        count = count,
        keyword = '',
        #want = {'id': None},
        each_fn = item_each_fn
    )
    if log_resp: logger.dump(test_youtube_search)


log.enable(level = log.levels.DEBUG)

thread.start([
    threading.Thread(target = tiktok_test),
    threading.Thread(target = youtube_test)
])
thread.join()
