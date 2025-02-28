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
        """
        Add two numbers using the cluster.

        :param x: First number
        :param y: Second number
        :return: Sum of the two numbers.
        """
        return asyncio.run(self.executor.execute_add(x, y))

    def urandom(self) -> bytes:
        """
        Test fetching a large, asynchronous result (random bytes)

        :return: The random bytes fetched
        """
        return asyncio.run(self.executor.execute_urandom())

    def register_transformation(self, func: bytes) -> str:
        """
        Register a transformation with the object store.

        :param func: Dumped (using dill) function representing a transformation. See DatasetBase.transform
        :return: The Object ID (uuid string) of the new transformation
        """
        random_uuid = uuid.uuid4()
        self.object_store.create_object(TRANSFORMATION_COLLECTION, random_uuid, func)

        return str(random_uuid)

    def add_transformation_path(self, path: str, transformations: list[str]) -> None:
        """
        Inform the lineage manager of a planned new lineage for a dataset.

        :param path: The name (path) of the distributed dataset.
        :param transformations: The series of planned transformations (in execution order)
        """
        self.lineage_manager.add_transformations(path, transformations)

    def cache_transformation_path(self, path: str, transformations: list[str]) -> None:
        """
        Tell the lineage manager to mark a certain lineage as a cache point.

        :param path: The name (path) of the distributed dataset.
        :param transformations: The series of transformations to be done; the last one is the cache point.
        """
        prefixes_to_materialize = self.lineage_manager.materialize_transformations(path, transformations)

        raise NotImplementedError(f"cache_transformation_path({path}, {repr(transformations)})")
