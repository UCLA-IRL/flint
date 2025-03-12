"""
Client library used on local machine by end-users, "core interface", calls ndn_compute_remote via RPC
"""

from xmlrpc.client import ServerProxy
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Self, Optional
import os
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

    def urandom(self) -> bytes:
        """
        Test fetching a large, asynchronous result (random bytes)

        :return: The random bytes fetched
        """
        return self.proxy.urandom()

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
        def map(self, func: Callable) -> Self:
            """
            Lazily perform a distributed map transformation on a distributed dataset.

            Equivalent to: df_1 = df_0.map(func)

            :param func: Function passed to pandas.DataFrame.map
            """
            pass

        @abstractmethod
        def filter(self, func: Callable) -> Self:
            """
            Lazily perform a distributed filter transformation on a distributed dataset.

            Equivalent to: df_1 = df_0[df_0.apply(my_predicate, axis=1)].reset_index(drop=True)

            :param func: Predicate function passed to pandas.DataFrame.apply
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

            Equivalent to: return df.agg(func)

            :param func: function, list, or label -> function dict describing the aggregation
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
                self._path = os.path.normpath(path)
                self._transformations = [] if transformations is None else transformations
                self._client = client

            def transform(self, func: Callable) -> Self:
                transformation_id = self._client.proxy.register_transformation(dill.dumps(func))

                transformations_updated = [*self._transformations, transformation_id]
                self._client.proxy.add_transformation_path(self._path, transformations_updated)

                return Dataset(self._path, self._client, transformations_updated)

            def map(self, func: Callable) -> Self:
                return self.transform(lambda df: df.map(func))

            def filter(self, func: Callable) -> Self:
                return self.transform(lambda df: df[df.apply(func, axis=1)].reset_index(drop=True))

            def cache(self) -> Self:
                print(self._client.proxy.cache_transformation_path(self._path, self._transformations))

                transformations_copy = list(self._transformations)
                return Dataset(self._path, self._client, transformations_copy)

            def reduce(self, func: Callable) -> pd.DataFrame:
                raise NotImplementedError("reduce")

            def collect(self) -> pd.DataFrame:
                raise NotImplementedError("collect")

            def for_each(self, func: Callable) -> None:
                raise NotImplementedError("for_each")

        return Dataset(path, self)
