from ndn_compute_base import NdnComputeBase
from xmlrpc.client import ServerProxy


class NdnComputeClient(NdnComputeBase):
    def __init__(self, url: str = 'http://localhost:5214/'):
        self.proxy = ServerProxy(url)

    def add(self, x: int, y: int) -> int:
        return self.proxy.add(x, y)
