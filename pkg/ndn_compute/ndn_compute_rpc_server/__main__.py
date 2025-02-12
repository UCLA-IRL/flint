import asyncio
import os
import signal
import sys
from typing import Optional
from ndn.appv2 import NDNApp
from ndn.transport.udp_face import UdpFace
from xmlrpc.server import SimpleXMLRPCServer
from ndn_compute_remote import NdnComputeRemote

app: Optional[NDNApp] = None
server: Optional[SimpleXMLRPCServer] = None


def handle_signal(signal_num, frame):
    if server is not None:
        server.shutdown()

    if app is not None:
        app.shutdown()

    sys.exit(0)


async def serve_rpc() -> None:
    if app is None:
        print("NDN app was not constructed, exiting")
        return

    management_port = int(os.environ.get("MANAGEMENT_PORT", "5000"))

    print(f"Driver running at {management_port} (may also be forwarded to host machine)", flush=True)

    global server
    server = SimpleXMLRPCServer(("0.0.0.0", management_port))
    server.register_instance(NdnComputeRemote(app))
    server.serve_forever()


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal) # Ctrl+C

    face = UdpFace('nfd1')

    global app
    app = NDNApp(face)
    app.run_forever(after_start=serve_rpc())


if __name__ == "__main__":
    main()
