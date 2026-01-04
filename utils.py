from rich.console import Console

import time
from contextlib import contextmanager

console = Console()

@contextmanager
def benchmark(label: str = "Block"):
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        elapsed = end - start
        print(f"{label} took {elapsed:.6f} seconds")