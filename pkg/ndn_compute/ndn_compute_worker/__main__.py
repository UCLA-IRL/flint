import os
import time
from typing import Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.transport.udp_face import UdpFace
from ndn.encoding import BinaryStr, FormalName, Component, Name
from ndn.security import NullSigner
from python_ndn_ext import announce_prefix

time.sleep(1)
print("Worker awake", flush=True)
app = NDNApp(UdpFace('nfd1'))
app_prefix = os.environ.get("APP_PREFIX")


# TODO: business logic should not be in __main__...
# @app.route(f'/{app_prefix}/add')
# Temporary note: we don't use the app.route decorator for a few reasons:
#   1. We want to announce sharded files by fragment granularity (a.log/1, a.log/5), but have one handler for all files
#   2. Routing security :)
# Use announce_prefix and attach_handler instead (see below)
def on_add_interest(name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc, context: PktContext) -> None:
    sum_int = (int(bytes(Component.get_value(name[2]))) +
               int(bytes(Component.get_value(name[3]))))
    print("name is", Name.to_str(name))
    print("sum found", sum_int, flush=True)
    sum_bytes = str(sum_int).encode('utf-8')
    data = app.make_data(name, sum_bytes, NullSigner())

    reply(data)


# TODO: business logic should not be in __main__...
async def trivial_app():
    await announce_prefix(app, f'/{app_prefix}/add', NullSigner())
    app.attach_handler(f'/{app_prefix}/add', on_add_interest)


if __name__ == '__main__':
    app.run_forever(after_start=trivial_app())
