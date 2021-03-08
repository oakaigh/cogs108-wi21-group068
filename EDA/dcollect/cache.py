import os
import sys
import shelve
import atexit
import threading

_base_path = os.path.dirname(__file__)

this = sys.modules[__name__]
if not hasattr(this, 'db'):
    this.db = shelve.open(f'{_base_path}/cache/default.db', flag = 'c')

this.savers = []

class func:
    @staticmethod
    def loader(*args, **kwargs):
        def inner(func):
            func(this.db.get(kwargs['uid'], {}))
        return inner

    @staticmethod
    def saver(*args, **kwargs):
        def inner(func):
            this.savers.append((kwargs['uid'], func))
        return inner

def enable_db(*args, **kwargs):
    def inner(cl):
        load, save = kwargs['load'], kwargs['save']
        uid = kwargs['uid']

        load(cl, this.db.get(uid, {}))
        this.savers.append((uid, cl, save))

        return cl

    return inner

@atexit.register
def cleanup():
    if hasattr(this, 'db'):
        for uid, cl, save in this.savers:
            this.db[uid] = save(cl)
        this.db.close()
