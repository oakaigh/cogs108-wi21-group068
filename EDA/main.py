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
log_resp = True


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
    test_youtube_trending = youtube_o.video.trending(
        count = count,
        parts = [
            youtube.parts.ID,
            youtube.parts.SNIPPET,
            youtube.parts.STATS,
            youtube.parts.details.CONTENT
        ],
        #want = {'id': None},
        #drop = False,
        each_fn = item_each_fn
    )
    if log_resp: logger.dump(test_youtube_trending)

    logger.info('testing: youtube search')
    test_youtube_search = youtube_o.video.search(
        count = count,
        keyword = '',
        #want = {'id': None},
        each_fn = item_each_fn
    )
    if log_resp: logger.dump(test_youtube_search)

    logger.info('testing: youtube channels')
    test_youtube_channel_info = youtube_o.channel.info(
        id = ['UC8Zo5A8qICfNAzVGDY_VT7w', 'UC0VOyT2OCBKdQhF3BAbZ-1g'],
        parts = [
            youtube.parts.ID,
            youtube.parts.SNIPPET,
            youtube.parts.STATS,
            youtube.parts.details.CONTENT
        ],
        #want = {'id': None},
        each_fn = item_each_fn
    )
    if log_resp: logger.dump(test_youtube_channel_info)

def youtubei_test():
    youtubei_o = youtubei(
        modules = modules,
        headers = conf.get('headers')
    )

    test_youtubei_ipr = youtubei_o.initial_player_response(
        id = 'ur560pZKRfg'
    )
    if log_resp: logger.dump(test_youtubei_ipr)


log.enable(level = log.levels.DEBUG)

thread.start([
    #threading.Thread(target = tiktok_test),
    threading.Thread(target = youtube_test),
    #threading.Thread(target = youtubei_test)
])
thread.join()
