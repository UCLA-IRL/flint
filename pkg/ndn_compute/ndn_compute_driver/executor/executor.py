import asyncio
import os
import json
from ndn.appv2 import NDNApp
from ndn.encoding import Name, Component
from ndn.types import ValidResult, InterestNack, InterestTimeout, InterestCanceled, MetaInfo, ValidationFailure
from python_ndn_ext import fetch_segments_with_retry
from functools import reduce


async def all_valid(name, sig, ctx) -> ValidResult:
    return ValidResult.ALLOW_BYPASS


class DriverExecutor:
    """
    Class containing asyncio methods which ask workers to do certain tasks (such as obtaining one or more RDDs)
    through interests.
    """

    def __init__(self, app: NDNApp):
        self.app: NDNApp = app
        self.app_prefix = os.environ.get("APP_PREFIX")

        self.manifest = self._load_manifest() # given this weird bootstrapping idk what better to do here

    def _load_manifest(self, path = "/app/fs-manifest.json"):
        try:
            with open(path, "r") as f:
                print("successfully loaded manifest", flush=True)
                return json.loads(f.read())
        except FileNotFoundError:
            print(f"{path} not found", flush=True)
            return {}

    async def execute_add(self, x: int, y: int) -> int:
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

    async def execute_urandom(self) -> bytes:
        try:
            data_name, content, context = await self.app.express(
                # Interest Name
                f'/{self.app_prefix}/urandom',
                all_valid,
                must_be_fresh=True,
                can_be_prefix=False,
                # Interest lifetime in ms
                lifetime=6000)
        except InterestNack as e:
            # A NACK is received
            print(f'Nacked with reason={e.reason}', flush=True)
            return bytes(b'2')
        except InterestTimeout:
            # Interest times out
            print(f'Timeout')
            return bytes(b'3')
        except InterestCanceled:
            # Connection to NFD is broken
            print(f'Canceled')
            return bytes(b'4')
        except ValidationFailure:
            # Validation failure
            print(f'Data failed to validate')
            return bytes(b'5')

        result_bytes = bytearray()
        try:
            async for segment in fetch_segments_with_retry(self.app,
                                                           Name.from_str(f'/{self.app_prefix}/result/urandom'),
                                                           all_valid):
                result_bytes.extend(segment)

            return bytes(result_bytes)
        except InterestTimeout:
            # Interest times out
            print(f'Timeout')
            return bytes(b'7')
        except InterestCanceled:
            # Connection to NFD is broken
            print(f'Canceled')
            return bytes(b'8')
        except ValidationFailure:
            # Validation failure
            print(f'Data failed to validate')
            return bytes(b'9')
        
    async def _execute_one_shard(self, path: str, shard: str, transformations: str):
        try:
            print(f'SENDING INTEREST: /{self.app_prefix}/request/{path}/{shard}/32=LINEAGE/32=TRANSFORMATIONS/{transformations}/32=END', flush=True)
            data_name, content, context = await self.app.express(
                # Interest Name
                f'/{self.app_prefix}/request/{path}/{shard}/32=LINEAGE/32=TRANSFORMATIONS/{transformations}/32=END',
                all_valid,
                must_be_fresh=False,
                can_be_prefix=False,
                # Interest lifetime in ms
                lifetime=6000)
            # Print out Data Name, MetaInfo and its content.
            print(f'Received Data Name: {Name.to_str(data_name)}', flush=True)
            return 10
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
    
    async def _collect_one_shard(self, path: str, shard: str, transformations: str):
        result_bytes = bytearray()
        try:
            async for segment in fetch_segments_with_retry(self.app,
                                                           Name.from_str(f'/{self.app_prefix}/result/{path}/{shard}/32=LINEAGE/32=TRANSFORMATIONS/{transformations}/32=END'),
                                                           all_valid):
                result_bytes.extend(segment)

            return bytes(result_bytes)
        except InterestTimeout:
            # Interest times out
            print(f'Timeout')
            return bytes(b'7')
        except InterestCanceled:
            # Connection to NFD is broken
            print(f'Canceled')
            return bytes(b'8')
        except ValidationFailure:
            # Validation failure
            print(f'Data failed to validate')
            return bytes(b'9')

    async def execute_transformations(self, path: str, transformations: list[str]):
        # given: path of some distributed file (ok sure)
        # transformations: list of uuid
        # target name: /(app Name)/request/(file path)/(shard num)/32=LINEAGE/32=TRANSFORMATIONS/(transformation1)/(transformation2)/…/32=END
        transformations_as_path = "/".join(transformations)
        return await asyncio.gather(*[self._execute_one_shard(path, str(shard), transformations_as_path)
                            for shard in list(map(lambda y: list(map(lambda c: c["sequence"], y["chunks"])),
                                                  filter(lambda x: x["filePath"] == path, self.manifest)))[0]])
    
    async def execute_collect(self, path: str, transformations: list[str]):
        await self.execute_transformations(path, transformations)  # request the transformations (if not done already)

        transformations_as_path = "/".join(transformations)
        lst = await asyncio.gather(*[self._collect_one_shard(path, str(shard), transformations_as_path)
                            for shard in list(map(lambda y: list(map(lambda c: c["sequence"], y["chunks"])),
                                                  filter(lambda x: x["filePath"] == path, self.manifest)))[0]])
        b = bytearray()
        for l in lst:
            b.extend(l)
        return b
