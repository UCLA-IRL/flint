import asyncio
import os
import zlib
from ndn.appv2 import NDNApp
from ndn_compute_worker.result_store import WorkerResultStore
from ndn.encoding import FormalName


class WorkerCompute:
    """
    Asynchronous methods that materialize RDDs, then saves them in the result store (which makes them available)
    """
    def __init__(self, app: NDNApp, result_store: WorkerResultStore):
        self._app = app
        self._result_store = result_store

    async def compute_urandom(self, name: FormalName) -> None:
        """
        Makes random bytes (with a sleep to simulate an asyncio operation such as an object store query)

        :param name: The name of the result (not the request) - in a non-exemplar method this would be parsed to
                     determine what work to do.
        """
        await asyncio.sleep(2)
        random_bytes = os.urandom(64 * 1024 * 1024)  # 64 MB

        print(f"urandom computed, hash should be {zlib.crc32(random_bytes)}")

        self._result_store.add_result(name, random_bytes)
