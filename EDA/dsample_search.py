from . import utils
import pandas as pd
import os
import logging

from .dcollect import plugins
from .dcollect import api_youtube as youtube
from .dcollect import api_youtubei as youtubei

modules = {'http': plugins.fasthttp()}
headers = None

# This key is for testing ONLY. DO NOT release to the public!
api_experiment = False
api_key_testing = None
api_key = os.environ.get('YOUTUBE_API_KEY') or api_key_testing

if not api_key:
    api_key = os.environ.get('YOUTUBE_EXPLORER_API_KEY')
    if api_key:
        api_experiment = True
    else:
        api_key = input('YouTube Data API Key: ')
        api_experiment = (input('Is this an explorer key? [Y/N]: ') == 'Y')

dataset_id = os.environ.get('DATASET_NAME')
if dataset_id == None:
    dataset_id = input('Dataset Name: ')

sample_size_per_query_default = 1000000
sample_size_per_query = os.environ.get('SAMPLE_SIZE_PER_QUERY')
if sample_size_per_query == None:
    sample_size_per_query = input('Sample size per query: ') or sample_size_per_query_default

sample_size_per_query = int(sample_size_per_query)

# create a YouTube API object
youtube_o = youtube.api(
    modules = modules,
    headers = headers,
    key = api_key,
    experiment = api_experiment
)

# create a YouTube Internals API object
youtubei_o = youtubei.api(
    modules = modules,
    headers = headers
)

pickle_proto = 3
dataset = utils.EDA.dataset(f'dsamples/youtube_search_{dataset_id}.dataset')

def df_search_gen(*args, **kwargs):
    from .dcollect.utils.log import log
    log.enable(level = log.levels.WARNING)
    import concurrent.futures

    df_search = None
    df_info = None
    df_channels = None
    df_ads = None

    def worker_df_search(*args, **kwargs):
        nonlocal df_search
        df_search = utils.dataframe.df_from_json(
            youtube_o.video.search(
                *args, **kwargs
            )
        )

    def worker_df_info():
        nonlocal df_info
        df_info = utils.dataframe.df_from_json(
            youtube_o.video.info(
                id = df_search['id']
            )
        )

    def worker_df_ads():
        nonlocal df_ads
        df_ads = utils.dataframe.df_from_json(
            youtubei_o.ad.placements(
                id = df_search['id'],
                throttle_size = 10
            )
        )

    def worker_df_channels():
        nonlocal df_channels
        df_channels = utils.dataframe.df_from_json(
            youtube_o.channel.info(
                id = df_search['creator.id']
            )
        )

    # - search
    worker_df_search(*args, **kwargs)

    workers = [worker_df_info, worker_df_ads, worker_df_channels]
    with concurrent.futures.ThreadPoolExecutor(max_workers = len(workers)) as executor:
        for worker in workers:
            executor.submit(worker)

    return df_search, df_info, df_channels, df_ads

def df_search_gen_bulk(paramlist: list):
    import concurrent.futures

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers = len(paramlist)) as executor:
        futures = [executor.submit(df_search_gen, **param) for param in paramlist]

    return [f.result() for f in futures]

import string

param_default = {
    'count': sample_size_per_query
}

paramlist = []
for c in string.ascii_lowercase:
    param = dict(param_default)
    param.update({
        'keyword': c
    })
    paramlist.append(param)

df_search = pd.DataFrame()
df_info = pd.DataFrame()
df_channels = pd.DataFrame()
df_ads = pd.DataFrame()

results = df_search_gen_bulk(paramlist)

def transpose(l):
    return list(map(list, zip(*l)))

df_search_res, df_info_res, df_channels_res, df_ads_res = transpose(results)

df_search = pd.concat(df_search_res, copy = False)
df_info = pd.concat(df_info_res, copy = False)
df_channels = pd.concat(df_channels_res, copy = False)
df_ads = pd.concat(df_ads_res, copy = False)

dataset.update('youtube_search.pkl', df_search, overwrite = True, proto = pickle_proto)
dataset.update('youtube_search_info.pkl', df_info, overwrite = True, proto = pickle_proto)
dataset.update('youtube_search_ads.pkl', df_ads, overwrite = True, proto = pickle_proto)
dataset.update('youtube_search_channels.pkl', df_channels, overwrite = True, proto = pickle_proto)

# - * (filter)
def drop_common(df, df_other, *args, **kwargs):
    return df.drop(columns = df.columns & df_other.columns, *args, **kwargs)

# - search
df_search.set_index(['id'], inplace = True)
# - info
df_info.set_index(['id'], inplace = True)
# - channels
df_channels = df_channels.add_prefix('creator.')
df_channels.set_index(['creator.id'], inplace = True)
# - ads
df_ads.set_index(['id'], inplace = True)

# drop common columns to avoid clashing
# in this case, only `df_search` and `df_info` have merging conflicts
drop_common(df_search, df_info, inplace = True)

# - search (with details)
df_search_details = df_search.copy()
# - info
df_search_details = df_search_details.merge(
    df_info,
    right_index = True,
    left_on = 'id',
    copy = False
)
# - ads
df_search_details = df_search_details.merge(
    df_ads,
    right_index = True,
    left_on = 'id',
    copy = False
)

dataset.update('youtube_search_details.pkl', df_search_details, proto = pickle_proto)
