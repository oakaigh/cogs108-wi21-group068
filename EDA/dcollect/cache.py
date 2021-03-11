import os
import sys
import atexit

class db_base:
    def __init__(self):
        raise NotImplementedError

    def load(self, uid):
        raise NotImplementedError

    def save(self, uid, data):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def __del__(self):
        self.close()

class pickledb(db_base):
    import os
    import pickle
    import portalocker

    def __init__(self, path, protocol = 3):
        self.path = path
        self.os.makedirs(path, exist_ok = True)
        self.proto = protocol

    def _read_raw(self, path):
        return open(path, 'rb')

    def _write_raw(self, path):
        return self.portalocker.Lock(path, 'wb+')

    def _write_pickle(self, path, data):
        with self._write_raw(path) as f:
            self.pickle.dump(data, f, protocol = self.proto)

    # credit: @aaron-hall
    def _read_pickle(self, path, default = None, write = False):
        if self.os.path.isfile(path):
            with self._read_raw(path) as f:
                try:
                    return self.pickle.load(f)
                except Exception as e:
                    raise e
        if write:
            self._write_pickle(path, default)
        return default

    def load(self, uid):
        return self._read_pickle(f'{self.path}/{uid}')

    def save(self, uid, data):
        return self._write_pickle(f'{self.path}/{uid}', data)

    def close(self):
        pass

this = sys.modules[__name__]
this.savers = []

_base_path = f'{os.path.dirname(__file__)}/cache'
_db_backend = pickledb

if not hasattr(this, 'db'):
    this.db = _db_backend(f'{_base_path}/default.cache')

def enable_db(*args, **kwargs):
    def inner(cl):
        load, save = kwargs['load'], kwargs['save']
        uid = kwargs['uid']

        if load:
            load(cl, this.db.load(uid))
        if save:
            this.savers.append((uid, cl, save))

        return cl

    return inner

@atexit.register
def cleanup():
    if hasattr(this, 'db'):
        for uid, cl, save in this.savers:
            this.db.save(uid, save(cl))
        this.db.close()
