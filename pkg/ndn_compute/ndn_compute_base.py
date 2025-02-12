from abc import ABC, abstractmethod


class NdnComputeBase(ABC):
    @abstractmethod
    def add(self, x: int, y: int) -> int:
        pass
