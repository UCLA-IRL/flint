import asyncio
import zlib
from ndn.appv2 import NDNApp
from ndn.security import NullSigner
from ndn.encoding import FormalName, Name
from python_ndn_ext import announce_prefix


class WorkerResultStore:
    """
    Stores and announces distributed datasets, evicts as necessary

    MUST be run as *synchronous* code called from an existing event loop
    """
    def __init__(self, app: NDNApp, segment_size: int = 1024, memory_limit: int = 1024 * 1024 * 1024):
        self._app: NDNApp = app
        self._segment_size = segment_size
        self._memory_limit: int = memory_limit
        self._memory_used: int = 0
        self._usage_history: list[int] = []
        self._store: dict[int, bytes] = dict()
        self._names: dict[int, FormalName] = dict()

    def add_result(self, name: FormalName, result: bytes) -> None:
        name_hash = zlib.crc32(Name.to_str(name).encode())

        self._memory_used += len(result)
        self._store[name_hash] = result
        self._names[name_hash] = name
        self._usage_history.insert(0, name_hash)

        asyncio.create_task(announce_prefix(self._app, name, NullSigner()))

        if self._memory_used > self._memory_limit:
            self._evict()

    def get_result_segment(self, name: FormalName, segment: int) -> (bytes, int):
        name_hash = zlib.crc32(Name.to_str(name).encode())

        if name_hash not in self._names:
            raise Exception(f"Result is not in store or has been evicted: {name}")

        self._usage_history.remove(name_hash)
        self._usage_history.insert(0, name_hash)

        result = self._store[name_hash]

        start_offset = segment * self._segment_size
        if segment < 0 or start_offset >= len(result):
            raise Exception("Segment is out of range")

        end_offset = min((segment + 1) * self._segment_size, len(result))

        final_segment = (len(result) // self._segment_size) - 1
        if len(result) % self._segment_size:
            final_segment += 1

        return result[start_offset:end_offset], final_segment

    def _evict(self):
        if len(self._usage_history) <= 1:
            return

        while self._memory_used > self._memory_limit:
            name_hash = self._usage_history.pop()

            self._memory_used -= len(self._store[name_hash])
            self._store.pop(name_hash)

            name = self._names[name_hash]
            self._names.pop(name_hash)

            asyncio.create_task(self._app.unregister(name))
