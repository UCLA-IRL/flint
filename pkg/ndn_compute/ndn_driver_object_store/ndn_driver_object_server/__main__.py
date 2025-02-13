import argparse
import os
import time
from uuid import UUID
from typing import Optional
from ndn_driver_object_store import NdnDriverObjectStore
from ndn.transport.udp_face import UdpFace
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.encoding import BinaryStr, FormalName, Component
from ndn.security import NullSigner


time.sleep(1)
print("Object store awake", flush=True)
app = NDNApp(UdpFace('nfd1'))

object_store: Optional[NdnDriverObjectStore] = None
app_prefix = os.environ.get("APP_PREFIX")


@app.route(f'/{app_prefix}/object/')
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


def main(database: str, collections: list[str]):
    global object_store
    object_store = NdnDriverObjectStore(database, collections)

    app.run_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=str, required=True)
    parser.add_argument("--collections", nargs='+', type=str, required=True)

    args = parser.parse_args()
    main(args.database, args.collections)