import asyncio
from typing import Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.transport.udp_face import UdpFace
from ndn.encoding import BinaryStr, FormalName, Component, Name, MetaInfo, make_data
from ndn.security import NullSigner
from ndn_compute_worker.result_store import WorkerResultStore
from ndn_compute_worker.compute import WorkerCompute


class WorkerHandler:
    """
    Contains methods (interest handlers) to handle interests to a worker.
    """
    def __init__(self, compute: WorkerCompute, result_store: WorkerResultStore):
        self._compute = compute
        self._result_store = result_store

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

    def on_urandom_interest(self, name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc,
                        context: PktContext) -> None:
        data = make_data(name, MetaInfo(), bytes(), NullSigner())
        result_name = [name[0]] + Name.from_str('/result/urandom')  # This is bad code, don't copy it.

        if not self._result_store.has_result(result_name):
            asyncio.create_task(self._compute.compute_urandom(result_name))

        reply(data)

    def on_result_interest(self, name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc,
                        context: PktContext) -> None:
        """
        Special interest handler used to return segmented result data stored in the result store.
        """
        result_name = name[:-1]
        segment = Component.to_number(name[-1])

        data = make_data(name + [Component.from_str('nack')], MetaInfo(), bytes(), NullSigner())
        try:
            segment_bytes, final_segment = self._result_store.get_result_segment(result_name, segment)
            data = make_data(name, MetaInfo(final_block_id=Component.from_segment(final_segment)),
                             segment_bytes, NullSigner())
        except Exception as e:
            print(f"NACKed result interest {name}: {e}")

        reply(data)
