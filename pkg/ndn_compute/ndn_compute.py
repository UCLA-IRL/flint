from abc import ABC, abstractmethod


class NdnCompute(ABC):
    @abstractmethod
    def add(self, x: int, y: int) -> int:
        pass
