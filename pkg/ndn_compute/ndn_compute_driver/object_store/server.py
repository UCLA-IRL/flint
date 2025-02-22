"""
Serve the object store as an NDN App accepting interests for objects.
"""

import argparse
import os
import time
from uuid import UUID
from typing import Optional
from ndn_compute_driver.object_store import DriverObjectStore
from ndn.transport.udp_face import UdpFace
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.encoding import BinaryStr, FormalName, Component
from ndn.security import NullSigner
from python_ndn_ext import announce_prefix


time.sleep(1)
print("Object store awake", flush=True)
app = NDNApp(UdpFace('nfd1'))

object_store: Optional[DriverObjectStore] = None
app_prefix = os.environ.get("APP_PREFIX")


def on_object_interest(name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc, context: PktContext) -> None:
    collection = bytes(Component.get_value(name[2])).decode('utf-8')
    object_id = UUID(bytes(Component.get_value(name[3])).decode('utf-8'))

    result_bytes = bytes()
    try:
        result_bytes = object_store.retrieve_object(collection, object_id)
    except Exception as e:
        print(f'Error while retrieving object: {e}', flush=True)

    data = app.make_data(name, result_bytes, NullSigner())

    reply(data)


async def object_server_setup():
    await announce_prefix(app, f'/{app_prefix}/object/', NullSigner())
    app.attach_handler(f'/{app_prefix}/object/', on_object_interest)


def main(database: str, collections: list[str]):
    global object_store
    object_store = DriverObjectStore(database, collections)

    app.run_forever(after_start=object_server_setup())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=str, required=True)
    parser.add_argument("--collections", nargs='+', type=str, required=True)

    args = parser.parse_args()
    main(args.database, args.collections)