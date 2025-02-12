from ndn_compute_base import NdnComputeBase
from ndn.encoding import Name


class NdnComputeRemote(NdnComputeBase):
    def add(self, x: int, y: int) -> int:
        return x + y
