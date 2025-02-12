import time
from typing import Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.transport.udp_face import UdpFace
from ndn.encoding import BinaryStr, FormalName, Component, Name
from ndn.security import NullSigner

time.sleep(1)
print("Worker awake", flush=True)
app = NDNApp(UdpFace('nfd1'))


# TODO: business logic should not be in __main__...
@app.route('/add')
def on_add_interest(name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc, context: PktContext) -> None:
    sum_int = (int(bytes(Component.get_value(name[1]))) +
               int(bytes(Component.get_value(name[2]))))
    print("name is", Name.to_str(name))
    print("sum found", sum_int, flush=True)
    sum_bytes = str(sum_int).encode('utf-8')
    data = app.make_data(name, sum_bytes, NullSigner())

    reply(data)


if __name__ == '__main__':
    app.run_forever()
