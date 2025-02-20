import asyncio
import os
import signal
import sys
from typing import Optional
from ndn.appv2 import NDNApp
from ndn.transport.udp_face import UdpFace
from xmlrpc.server import SimpleXMLRPCServer
from ndn_compute_remote import NdnComputeRemote
from ndn_driver_object_store import NdnDriverObjectStore

app: Optional[NDNApp] = None
server: Optional[SimpleXMLRPCServer] = None
object_store: Optional[NdnDriverObjectStore] = None


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
    object_store = NdnDriverObjectStore('/app/objects.db', ['Transformation'], True)
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
