import threading

class thread:
    pool = []

    @staticmethod
    def start(threads):
        for t in threads:
            t.start()
            thread.pool.append(t)

    @staticmethod
    def join():
        for t in thread.pool:
            t.join()
