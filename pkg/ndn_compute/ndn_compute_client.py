from xmlrpc.client import ServerProxy
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Self, Optional
import dill
import pandas as pd


class NdnComputeClient:
    def __init__(self, url: str = 'http://localhost:5214/'):
        self.proxy = ServerProxy(url, use_builtin_types=True, allow_none=True)

    def add(self, x: int, y: int) -> int:
        return self.proxy.add(x, y)

    class DatasetBase(ABC):
        @abstractmethod
        def transform(self, func: Callable) -> Self:
            pass

        @abstractmethod
        def cache(self) -> Self:
            pass

        @abstractmethod
        def reduce(self, func: Callable) -> pd.DataFrame:
            pass

        @abstractmethod
        def collect(self) -> pd.DataFrame:
            pass

        @abstractmethod
        def for_each(self, func: Callable) -> None:
            pass

    def create_dataset(self, path: str) -> DatasetBase:
        class Dataset(self.DatasetBase):
            def __init__(self, path: str, client: NdnComputeClient, transformations: Optional[list[str]] = None):
                self._path = path
                self._transformations = [] if transformations is None else transformations
                self._client = client

            def transform(self, func: Callable) -> Self:
                transformation_id = self._client.proxy.register_transformation(dill.dumps(func))

                transformations_updated = [*self._transformations, transformation_id]
                self._client.proxy.add_transformation_path(self._path, transformations_updated)

                return Dataset(self._path, self._client, transformations_updated)

            def cache(self) -> Self:
                self._client.proxy.cache_transformation_path(self._path, self._transformations)

                transformations_copy = list(self._transformations)
                return Dataset(self._path, self._client, transformations_copy)

            def reduce(self, func: Callable) -> pd.DataFrame:
                raise NotImplementedError("reduce")

            def collect(self) -> pd.DataFrame:
                raise NotImplementedError("collect")

            def for_each(self, func: Callable) -> None:
                raise NotImplementedError("for_each")

        return Dataset(path, self)
