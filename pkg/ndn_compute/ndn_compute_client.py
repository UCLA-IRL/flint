"""
Client library used on local machine by end-users, "core interface", calls ndn_compute_remote via RPC
"""

from xmlrpc.client import ServerProxy
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Self, Optional
import dill
import pandas as pd


class NdnComputeClient:
    """
    Used to reach a ndn_compute driver.
    """

    def __init__(self, url: str = 'http://localhost:5214/'):
        """
        :param url: Address of the remote RPC server
        """
        self.proxy = ServerProxy(url, use_builtin_types=True, allow_none=True)

    def add(self, x: int, y: int) -> int:
        """
        Add two numbers using the cluster.

        :param x: First number
        :param y: Second number
        :return: Sum of the two numbers.
        """
        return self.proxy.add(x, y)

    class DatasetBase(ABC):
        """
        Represents a distributed dataset and its operational/transformational lineage.
        """

        @abstractmethod
        def transform(self, func: Callable) -> Self:
            """
            Lazily perform a distributed transformation on a distributed dataset.

            Note that this is the "raw" method with no syntactic sugar, one passes in a lambda function that takes in a
            dataframe and returns a dataframe (not a row).

            Equivalent to: df_1 = func(df_0)

            :param func: A function with one argument (a dataframe) and which returns a dataframe.
            """
            pass

        @abstractmethod
        def cache(self) -> Self:
            """
            Provide a hint that the distributed dataset of the current lineage should be cached.
            """
            pass

        @abstractmethod
        def reduce(self, func: Callable) -> pd.DataFrame:
            """
            Perform a distributed reduce and obtain the result.

            Equivalent to: return df.groupby('key').apply(func)

            :param func: Function to pass to `apply` after the dataframe is grouped by the key.
            :return: The resulting dataframe
            """
            pass

        @abstractmethod
        def collect(self) -> pd.DataFrame:
            """
            Collect the distributed dataset and show it on this machine.

            Equivalent to: return df

            :return: The distributed dataset as a dataframe
            """
            pass

        @abstractmethod
        def for_each(self, func: Callable) -> None:
            """
            Perform an action (with side effects) on the distributed dataset

            Equivalent to: _ = df.map(func)

            :param func: The parameter with the side effect, called on each row
            """
            pass

    def create_dataset(self, path: str) -> DatasetBase:
        """
        Get a handle to a distributed dataset.

        :param path: Desired file path on the distributed workers (e.g., 'appA/events.log.jsonl')
        :return: The dataset object
        """
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
