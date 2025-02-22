import asyncio
import os
from ndn.appv2 import NDNApp
from ndn.encoding import Name
from ndn.types import ValidResult, InterestNack, InterestTimeout, InterestCanceled, ValidationFailure


class DriverExecutor:
    def __init__(self, app: NDNApp):
        self.app: NDNApp = app
        self.app_prefix = os.environ.get("APP_PREFIX")

    async def execute_add(self, x: int, y: int) -> int:
        async def all_valid(name, sig, ctx) -> ValidResult:
            return ValidResult.ALLOW_BYPASS

        try:
            data_name, content, context = await self.app.express(
                # Interest Name
                f'/{self.app_prefix}/add/{x}/{y}',
                all_valid,
                must_be_fresh=False,
                can_be_prefix=False,
                # Interest lifetime in ms
                lifetime=6000)
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
