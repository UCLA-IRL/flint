import asyncio
from ndn_compute_base import NdnComputeBase
from ndn.appv2 import NDNApp
from ndn.encoding import Name
from ndn.types import ValidResult, InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn_driver_object_store import NdnDriverObjectStore

import nest_asyncio
nest_asyncio.apply()


class NdnComputeRemote(NdnComputeBase):
    def __init__(self, app: NDNApp, object_store: NdnDriverObjectStore):
        self.app: NDNApp = app
        self.object_store: NdnDriverObjectStore = object_store

    def add(self, x: int, y: int) -> int:
        loop = asyncio.get_running_loop()

        async def all_valid(name, sig, ctx) -> ValidResult:
            return ValidResult.ALLOW_BYPASS

        try:
            data_name, content, context = asyncio.run(self.app.express(
                # Interest Name
                f'/add/{x}/{y}',
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

