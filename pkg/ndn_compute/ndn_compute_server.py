from ndn_compute import NdnCompute
from ndn.encoding import Name


class NdnComputeServer(NdnCompute):
    def add(self, x: int, y: int) -> int:
        return x + y
