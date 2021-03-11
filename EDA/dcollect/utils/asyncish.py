import asyncio
import functools


def default_loop():
    return asyncio.get_event_loop()

# credit @0xbf
def async_wraps(func):
    @functools.wraps(func)
    async def run(*args, loop = None, executor = None, **kwargs):
        if loop is None:
            loop = default_loop()
        pfunc = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run
