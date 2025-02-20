import asyncio
import os
import uuid
from ndn.appv2 import NDNApp
from ndn.encoding import Name
from ndn.types import ValidResult, InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn_driver_object_store import NdnDriverObjectStore

import nest_asyncio
nest_asyncio.apply()


TRANSFORMATION_COLLECTION = "Transformation"


class NdnComputeRemote:
    def __init__(self, app: NDNApp, object_store: NdnDriverObjectStore):
        self.app: NDNApp = app
        self.object_store: NdnDriverObjectStore = object_store
        self.app_prefix = os.environ.get("APP_PREFIX")

    def add(self, x: int, y: int) -> int:
        loop = asyncio.get_running_loop()

        async def all_valid(name, sig, ctx) -> ValidResult:
            return ValidResult.ALLOW_BYPASS

        try:
            data_name, content, context = asyncio.run(self.app.express(
                # Interest Name
                f'/{self.app_prefix}/add/{x}/{y}',
                all_valid,
                must_be_fresh=False,
                can_be_prefix=False,
                # Interest lifetime in ms
                lifetime=6000))
            # Print out Data Name, MetaInfo and its content.
            print(f'Received Data Name: {Name.to_str(data_name)}', flush=True)
            # print(context)
            print(bytes(content) if content else None)
            return int(bytes(content).decode('utf-8'))
        except InterestNack as e:
            # A NACK is received
            print(f'Nacked with reason={e.reason}', flush=True)
            return -2
        except InterestTimeout:
            # Interest times out
            print(f'Timeout')
            return -3
        except InterestCanceled:
            # Connection to NFD is broken
            print(f'Canceled')
            return -4
        except ValidationFailure:
            # Validation failure
            print(f'Data failed to validate')
            return -5

    def register_transformation(self, func: bytes) -> str:
        random_uuid = uuid.uuid4()
        self.object_store.create_object(TRANSFORMATION_COLLECTION, random_uuid, func)

        return str(random_uuid)

    def add_transformation_path(self, path: str, transformations: list[str]) -> None:
        raise NotImplementedError(f"add_transformation_path({path}, {repr(transformations)})")

    def cache_transformation_path(self, path: str, transformations: list[str]) -> None:
        raise NotImplementedError(f"cache_transformation_path({path}, {repr(transformations)})")
