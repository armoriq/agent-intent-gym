from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path

from .models import BenchmarkConfig
from .runner import run_benchmark
from .store import BenchmarkStore


async def main():
    config_file, root, run_id, stop_path = sys.argv[1:]
    config = BenchmarkConfig.model_validate_json(Path(config_file).read_text())
    stop = threading.Event()
    if Path(stop_path).exists():
        stop.set()

    async def watch():
        while True:
            if Path(stop_path).exists():
                stop.set()
                return
            await asyncio.sleep(0.25)

    watcher = asyncio.create_task(watch())
    try:
        await run_benchmark(config, BenchmarkStore(root), stop=stop, run_id=run_id)
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
