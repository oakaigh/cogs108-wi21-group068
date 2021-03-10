import IPython
import IPython.display as disp


IPython.core.interactiveshell.\
    InteractiveShell.ast_node_interactivity = "all"

def clear():
    disp.clear_output(wait = True)

def output(disp_os):
    for d in disp_os:
        disp.display(d)

def results_report(disp_os, name = ''):
    output([
            disp.Markdown('---'),
            disp.Markdown(f'# Results - {name}')
        ] + disp_os +
        [disp.Markdown('---')]
    )


import hashlib

def md5_encode(s: str):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def as_fname(s: str):
    return md5_encode(s)

try:
    import pandas as pd
except ImportError:
    print('`python3 -m pip install pandas` or have bad luck')

def df_from_json(items, *args, **kwargs):
    return pd.json_normalize(items, *args, **kwargs)

def df_report(dfs, full = False, *args, **kwargs):
    dfs = [dfs] if not isinstance(dfs, list) else dfs
    for df in dfs:
        results_report([
            disp.Markdown('## Data Preview'),
            df.head() if not full else df,
            disp.Markdown('## Stats'),
            df.describe()
        ], *args, **kwargs)

def df_report_from_json(items, name = '', full = False, *args, **kwargs):
    return df_report(df_from_json(items, *args, **kwargs), name = name, full = full)

def df_drop_duplicates(df, level = None, *args, **kwargs):
    indices = df.index
    if not level == None:
        indices = indices.get_level_values(level)
    return df[~indices.duplicated(*args, **kwargs)]

def df_load_pickle(fname, *args, **kwargs):
    return pd.read_pickle(fname, *args, **kwargs)

def df_update_pickle(df, fname, proto = 3, *args, **kwargs):
    import os

    df_updated = None
    if os.path.isfile(fname):
        df_updated = df_load_pickle(fname)
        df_updated = df.combine_first(
            other = df_updated
        )
    else:
        df_updated = df

    df_updated.to_pickle(fname, protocol = proto, *args, **kwargs)
