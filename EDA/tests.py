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

def item_each_fn(item):
    logger.dump(item)

def res_fn(res):
    if log_resp: logger.dump(res)


def tiktok_test():
    tiktok_o = tiktok.api(
        modules = modules,
        headers = conf.get('headers')
    )

    for item in tiktok_o.video.trending(
        count = count,
        on_result = res_fn
    ):
        item_each_fn(item)

def youtube_test():
    youtube_o = youtube.api(
        modules = modules,
        key = 'AIzaSyBKsF33Y1McGDdBWemcfcTbVyJu23XDNIk',
        headers = conf.get('headers')
    )

    logger.info('testing: youtube trending')
    for item in youtube_o.video.trending(
        count = count,
        parts = [
            youtube.res_parts.ID,
            youtube.res_parts.SNIPPET,
            youtube.res_parts.STATS,
            youtube.res_parts.details.CONTENT
        ],
        #want = {'id': None},
        on_result = res_fn
    ):
        item_each_fn(item)

    logger.info('testing: youtube trending (parts == None)')
    for item in youtube_o.video.trending(
        count = count,
        parts = None,
        want = {'id': None},
        on_result = res_fn
    ):
        item_each_fn(item)

    logger.info('testing: youtube search')
    for item in youtube_o.video.search(
        count = count,
        keyword = '',
        #want = {'id': None},
        on_result = res_fn
    ):
        item_each_fn(item)

    logger.info('testing: youtube channels')
    for item in youtube_o.channel.info(
        id = ['UC8Zo5A8qICfNAzVGDY_VT7w', 'UC0VOyT2OCBKdQhF3BAbZ-1g'],
        parts = [
            youtube.res_parts.ID,
            youtube.res_parts.SNIPPET,
            youtube.res_parts.STATS,
            youtube.res_parts.details.CONTENT
        ],
        #want = {'id': None},
        on_result = res_fn
    ):
        item_each_fn(item)

    logger.info('testing: youtube channels (parts == None)')
    for item in youtube_o.channel.info(
        id = ['UC8Zo5A8qICfNAzVGDY_VT7w', 'UC0VOyT2OCBKdQhF3BAbZ-1g'],
        #parts = None,
        #want = {'id': None},
        on_result = res_fn
    ):
        item_each_fn(item)

def youtubei_test():
    youtubei_o = youtubei.api(
        modules = modules,
        headers = conf.get('headers')
    )

    '''
    logger.info('testing: youtube initial player response')
    for item in youtubei_o.initial_player_response(
        id = 'ur560pZKRfg'
    ):
        item_each_fn(item)
    '''

    logger.info('testing: youtube ad placements')
    for item in youtubei_o.ad.placements(
        id = 'ur560pZKRfg',
        on_result = res_fn
    ):
        item_each_fn(item)


log.enable(level = log.levels.DEBUG)

thread.start([
    threading.Thread(target = tiktok_test),
    threading.Thread(target = youtube_test),
    threading.Thread(target = youtubei_test)
])
thread.join()
