"""
Entry points for nodes acting as workers. The entry point is responsible for starting an NDN app listening for RDD
interests.
"""

import os
import time
from ndn.appv2 import NDNApp
from ndn.transport.udp_face import UdpFace
from ndn.security import NullSigner
from ndn_compute_worker.handler import WorkerHandler
from ndn_compute_worker.result_store import WorkerResultStore
from ndn_compute_worker.compute import WorkerCompute
from python_ndn_ext import announce_prefix

time.sleep(1)
print("Worker awake", flush=True)
app = NDNApp(UdpFace('nfd1'))
app_prefix = os.environ.get("APP_PREFIX")


# Temporary note: we don't use the app.route decorator for a few reasons:
#   1. We want to announce sharded files by fragment granularity (a.log/1, a.log/5), but have one handler for all files
#   2. Routing security :)
# Use announce_prefix and attach_handler instead (see below)


async def worker():
    result_store = WorkerResultStore(app)
    compute = WorkerCompute(app, result_store)
    handler = WorkerHandler(compute, result_store)
    # NOTE: result prefix is not announced, as results that have been made available will be announced with a more
    # specific prefix at that time in the future.
    app.attach_handler(f'/{app_prefix}/result', handler.on_result_interest)

    await announce_prefix(app, f'/{app_prefix}/urandom', NullSigner())
    app.attach_handler(f'/{app_prefix}/urandom', handler.on_urandom_interest)

    await announce_prefix(app, f'/{app_prefix}/add', NullSigner())
    app.attach_handler(f'/{app_prefix}/add', WorkerHandler.on_add_interest)


if __name__ == '__main__':
    app.run_forever(after_start=worker())
