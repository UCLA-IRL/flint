"""
Entry point for the node acting as a driver. The entry point is responsible for starting three
"processes": the object store server, the RPC server, and the executor's NDN app. Note that the RPC server and NDN app
live in the same process, thus requiring the use of nested asyncio. (Note that the previous sentences contradict with
the hierarchy of the layered diagram, as the diagram shows module interaction and *not* the process tree). The
aforementioned RPC server serves objects in the ndn_compute_remote module. In addition to serving ndn_compute_remote,
its submodules are used by ndn_compute_remote's classes.
"""

import asyncio
import os
import signal
import sys
from typing import Optional
from ndn.appv2 import NDNApp
from ndn.transport.udp_face import UdpFace
from xmlrpc.server import SimpleXMLRPCServer

from ndn_compute_driver.object_store import DriverObjectStore
from ndn_compute_remote import NdnComputeRemote


import nest_asyncio
nest_asyncio.apply()


app: Optional[NDNApp] = None
server: Optional[SimpleXMLRPCServer] = None
object_store: Optional[DriverObjectStore] = None


def handle_signal(signal_num, frame) -> None:
    if server is not None:
        server.shutdown()

    if app is not None:
        app.shutdown()

    if object_store is not None:
        object_store.shutdown()

    sys.exit(0)


def run_object_server() -> None:
    global object_store
    object_store = DriverObjectStore('/app/objects.db', ['Transformation'], True)
    object_store.serve_detached()


async def serve_rpc() -> None:
    if app is None:
        print("NDN app was not constructed, exiting")
        return

    management_port = int(os.environ.get("MANAGEMENT_PORT", "5000"))

    print(f"Driver running at {management_port} (may also be forwarded to host machine)", flush=True)

    global server
    server = SimpleXMLRPCServer(("0.0.0.0", management_port), use_builtin_types=True, allow_none=True)
    server.register_instance(NdnComputeRemote(app, object_store))
    server.serve_forever()


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal) # Ctrl+C

    run_object_server()

    face = UdpFace('nfd1')

    global app
    app = NDNApp(face)
    app.run_forever(after_start=serve_rpc())


if __name__ == "__main__":
    main()
