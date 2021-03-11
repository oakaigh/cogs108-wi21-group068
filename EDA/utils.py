class time:
    import datetime

    @staticmethod
    def datetime_range(
        dtype = datetime.datetime,
        *args, **kwargs
    ):
        return (
            dtype.min.replace(*args, **kwargs),
            dtype.max.replace(*args, **kwargs)
        )

class dataframe:
    try:
        import pandas as pd
    except ImportError:
        print('`python3 -m pip install pandas` or have bad luck')
    import os

    @staticmethod
    def df_from_json(items, *args, **kwargs):
        return dataframe.pd.json_normalize(items, *args, **kwargs)

    @staticmethod
    def df_drop_duplicates(df, level = None, *args, **kwargs):
        indices = df.index
        if not level == None:
            indices = indices.get_level_values(level)
        return df[~indices.duplicated(*args, **kwargs)]

    @staticmethod
    def df_load_pickle(fname, *args, **kwargs):
        return dataframe.pd.read_pickle(fname, *args, **kwargs)

    @staticmethod
    def df_update(df, other, *args, **kwargs):
        return other.combine_first(other = df)

    @staticmethod
    def df_update_pickle(
        df, fname,
        proto = 3, overwrite = False,
        *args, **kwargs
    ):
        df_updated = None
        if not overwrite and dataframe.os.path.isfile(fname):
            df_updated = dataframe.df_update(dataframe.df_load_pickle(fname), df)
        else:
            df_updated = df

        df_updated.to_pickle(fname, protocol = proto, *args, **kwargs)

class EDA:
    class dataset:
        import os

        def __init__(self, path):
            self.path = path
            self.os.makedirs(path, exist_ok = True)

        def load(self, name, *args, **kwargs):
            return dataframe.df_load_pickle(f'{self.path}/{name}', *args, **kwargs)

        def update(self, name, df, *args, **kwargs):
            return dataframe.df_update_pickle(df, f'{self.path}/{name}', *args, **kwargs)
