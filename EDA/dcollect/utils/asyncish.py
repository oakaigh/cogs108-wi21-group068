import asyncio
from functools import wraps, partial


# credit @0xbf
def async_wraps(func):
    @wraps(func)
    async def run(*args, loop = None, executor = None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run
