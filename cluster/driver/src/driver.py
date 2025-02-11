import os
from xmlrpc.server import SimpleXMLRPCServer
from ndn_compute_server import NdnComputeServer

management_port = int(os.environ.get("MANAGEMENT_PORT", "5000"))

print(f"Driver running at {management_port} (may also be forwarded to host machine)", flush=True)

server = SimpleXMLRPCServer(("0.0.0.0", management_port))
server.register_instance(NdnComputeServer())
server.serve_forever()
