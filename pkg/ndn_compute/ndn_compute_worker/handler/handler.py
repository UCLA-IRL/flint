from typing import Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.transport.udp_face import UdpFace
from ndn.encoding import BinaryStr, FormalName, Component, Name, MetaInfo, make_data
from ndn.security import NullSigner


class WorkerHandler:
    """
    Contains methods (interest handlers) to handle interests in RDDs.
    """
    @staticmethod
    def on_add_interest(name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc,
                        context: PktContext) -> None:
        sum_int = (int(bytes(Component.get_value(name[2]))) +
                   int(bytes(Component.get_value(name[3]))))
        print("name is", Name.to_str(name))
        print("sum found", sum_int, flush=True)
        sum_bytes = str(sum_int).encode('utf-8')
        data = make_data(name, MetaInfo(freshness_period=60 * 1_000), sum_bytes, NullSigner())

        reply(data)