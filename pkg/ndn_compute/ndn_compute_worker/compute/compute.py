import asyncio
import os
import zlib
import dill
import pandas as pd
from ndn.appv2 import NDNApp
from ndn_compute_worker.result_store import WorkerResultStore
from ndn.encoding import FormalName, Name
from ndn.types import ValidResult, InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from .utils import DeserializedTransformationInterest, attempt_interest, all_valid
from python_ndn_ext.segment_fetcher_v2 import fetch_segments
from io import BytesIO


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
        random_bytes = os.urandom(64 * 1024 * 1024)  # 64 MiB

        print(f"urandom computed, hash should be {zlib.crc32(random_bytes)}")

        self._result_store.add_result(name, random_bytes)

    async def compute_transform(self, name: FormalName, decoded_interest_name: DeserializedTransformationInterest) -> None:
        """
        Given a shard name, apply requisite transfomations

        :param name: Name of shard + transformations to apply
        :param decoded_interest_name: Individual components of interest name
        """
        # Get all transformations except for the very last one
        transformations = [*decoded_interest_name.transformations[:-1]]

        # List of transformations to apply, in order
        applying_transformations = [decoded_interest_name.transformations[-1]]

        # Flag to check if last transformation should be fetched from result store or network
        should_fetch_segments = False

        # Last name to fetch
        name_to_check = None

        # While there are transformations to check
        while len(transformations) > 0:
            trans = "/".join(transformations)
            name_to_check = Name.from_str(f"/{decoded_interest_name.app}/result/{decoded_interest_name.filepath}/{decoded_interest_name.shard}/32=LINEAGE/32=TRANSFORMATIONS/{trans}/32=END")

            # Check if result store has transformed data
            if self._result_store.has_result(name_to_check):
                break

            # Check if network has transformed data
            if await attempt_interest(self._app, name_to_check):
                should_fetch_segments = True
                break

            # If not, pop from the transformations list and try again
            applying_transformations.insert(0, transformations.pop())

        # Data to apply transformation to
        data = None

        # No transformations were found in the result store or network, must fetch from filesystem
        if len(transformations) == 0:
            with open(os.path.join("/app/data", decoded_interest_name.filepath, str(decoded_interest_name.shard)), "rb") as f:
                data = f.read()

        # Should get from network
        elif should_fetch_segments:
            try:
                async for seg in fetch_segments(self._app, name_to_check, all_valid):
                    if data is None:
                        data = seg
                    else:
                        data += seg
            except:
                print("Failed to fetch segments from network")
                return

        # Should get from result store
        else:
            try:
                for seg in self._result_store.get_result_segments(name_to_check):
                    if data is None:
                        data = seg
                    else:
                        data += seg
            except Exception as err:
                print("Failed to get segments from store")
                print(err)
                return
            
        # Read data as JSONL dataframe
        df = pd.read_json(BytesIO(data), lines=True)
        
        # Get requisite transformations from driver object store
        async def get_transformation(transformation: str) -> callable:
            _, content, _ = await self._app.express(
                # Interest Name
                f"/{decoded_interest_name.app}/object/Transformation/{transformation}",
                    all_valid,
                    must_be_fresh=False,
                    can_be_prefix=False,
                    # Interest lifetime in ms
                    lifetime=6000)

            return dill.loads(content)
            
        # Get each transformation function
        transform_funcs = await asyncio.gather(*map(get_transformation, applying_transformations))

        # Apply each transformation function to dataframe
        for f in transform_funcs:
            df = df.transform(f)

        # Place result in result store
        final_json = df.to_json(orient="records", lines=True)
        self._result_store.add_result(name, bytes(final_json, 'utf-8'))

        


