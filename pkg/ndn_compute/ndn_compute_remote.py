import asyncio
import uuid
from ndn.appv2 import NDNApp
from ndn_compute_driver.executor import DriverExecutor
from ndn_compute_driver.lineage_manager import LineageManager
from ndn_compute_driver.object_store import DriverObjectStore


TRANSFORMATION_COLLECTION = "Transformation"


class NdnComputeRemote:
    def __init__(self, app: NDNApp, object_store: DriverObjectStore):
        self.executor: DriverExecutor = DriverExecutor(app)
        self.lineage_manager: LineageManager = LineageManager()
        self.object_store: DriverObjectStore = object_store

    def add(self, x: int, y: int) -> int:
        return asyncio.run(self.executor.execute_add(x, y))

    def register_transformation(self, func: bytes) -> str:
        random_uuid = uuid.uuid4()
        self.object_store.create_object(TRANSFORMATION_COLLECTION, random_uuid, func)

        return str(random_uuid)

    def add_transformation_path(self, path: str, transformations: list[str]) -> None:
        raise NotImplementedError(f"add_transformation_path({path}, {repr(transformations)})")

    def cache_transformation_path(self, path: str, transformations: list[str]) -> None:
        raise NotImplementedError(f"cache_transformation_path({path}, {repr(transformations)})")
