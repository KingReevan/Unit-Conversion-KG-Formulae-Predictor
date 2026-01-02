import time
import asyncio
from functools import wraps

def timeit(func):
    if asyncio.iscoroutinefunction(func):
        # async wrapper
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            end = time.perf_counter()
            print(f"\n⏱️ Execution time for '{func.__name__}': {end - start:.4f} seconds\n")
            return result
        return async_wrapper

    else:
        # sync wrapper
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            print(f"\n⏱️ Execution time for '{func.__name__}': {end - start:.4f} seconds\n")
            return result
        return sync_wrapper
