import asyncio
from typing import Generator
import zlib
from ndn.appv2 import NDNApp
from ndn.security import NullSigner
from ndn.encoding import FormalName, Name, Signer
from python_ndn_ext import announce_prefix


class WorkerResultStore:
    """
    Stores and announces distributed datasets, evicts as necessary using LRU

    Note that the interest handler for results is NOT in this class, one should write their own handler. However, this
    class will announce the necessary prefixes for the specific data stored in the result store.

    MUST be run as *synchronous* code called from an existing event loop
    """
    def __init__(self, app: NDNApp, signer: Signer, segment_size: int = 1024, memory_limit: int = 2048 * 1024 * 1024):
        """
        :param app: NDN app in which to announce the result prefix
        :segment_size: The size (in bytes) of each segment to break the result into
        :memory_limit: The maximum size of results to store in RAM (results beyond the limit will be evicted).
        """
        self._app: NDNApp = app
        self._signer = signer
        self._segment_size = segment_size
        self._memory_limit: int = memory_limit
        self._memory_used: int = 0
        self._usage_history: list[int] = []
        self._store: dict[int, bytes] = dict()
        self._names: dict[int, FormalName] = dict()

    def add_result(self, name: FormalName, result: bytes) -> None:
        """
        Make a result available by storing it and announcing the name.

        NOTE: this method *may* evict older results if above the memory limit, but it will not evict the most recent one

        :param name: The name (should be the result name, not the request name) to announce, excluding the segment
        :param result: The content of the result, as bytes
        """
        name_hash = zlib.crc32(Name.to_str(name).encode())

        self._memory_used += len(result)
        self._store[name_hash] = result
        self._names[name_hash] = name
        self._usage_history.insert(0, name_hash)

        asyncio.create_task(announce_prefix(self._app, name, self._signer))

        if self._memory_used > self._memory_limit:
            self._evict()

    def has_result(self, name: FormalName) -> bool:
        """
        Check whether the result is (still) saved in the result store. Does not update LRU in any way.

        :param name: The result name to query, excluding the segment component
        :return: True if the result is in the result store, False otherwise
        """
        name_hash = zlib.crc32(Name.to_str(name).encode())

        return name_hash in self._names

    def get_result_segment(self, name: FormalName, segment: int) -> tuple[bytes, int]:
        """
        Obtain a portion of the result data, at a certain segment number. Updates the LRU.

        Note that the returned final segment number is inclusive (i.e., it is the last valid segment number)

        :param name: The result name to query, excluding the segment component
        :param segment: The (0-indexed) segment number
        :return: A tuple of (result data segment, final segment number)
        :raises Exception: Invalid segment number; the result is not in the store or has been evicted
        """
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
    
    def get_result_segments(self, name: FormalName) -> Generator[bytes, None, None]:
        """
        Same as `get_result_segment`, but in generator form. 
        :param name: The result name to query, excluding the segment component
        :param segment: The (0-indexed) segment number
        :return: Generator with all segments
        :raises Exception: Invalid segment number; the result is not in the store or has been evicted
        """

        cur_seg = 0
        first_seg, final_seg_num = self.get_result_segment(name, cur_seg)
        yield first_seg

        cur_seg += 1

        while cur_seg <= final_seg_num:
            seg, _ = self.get_result_segment(name, cur_seg)
            yield seg
            cur_seg += 1

    def _evict(self):
        while self._memory_used > self._memory_limit:
            if len(self._usage_history) <= 1:
                return

            name_hash = self._usage_history.pop()

            self._memory_used -= len(self._store[name_hash])
            self._store.pop(name_hash)

            name = self._names[name_hash]
            self._names.pop(name_hash)

            asyncio.create_task(self._app.unregister(name))
