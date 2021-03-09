import IPython
import IPython.display as disp
try:
    import pandas as pd
except ImportError:
    print('`python3 -m pip install pandas` or have bad luck')


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

def df_report(dfs, full = False, *args, **kwargs):
    dfs = [dfs] if not isinstance(dfs, list) else dfs
    for df in dfs:
        results_report([
            disp.Markdown('## Data Preview'),
            df.head() if not full else df,
            disp.Markdown('## Stats'),
            df.describe()
        ], *args, **kwargs)

def df_from_json(items, *args, **kwargs):
    return pd.json_normalize(items, *args, **kwargs)

def df_report_from_json(items, name = '', full = False, *args, **kwargs):
    return df_report(df_from_json(items, *args, **kwargs), name = name, full = full)
