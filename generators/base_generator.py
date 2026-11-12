from abc import ABC, abstractmethod
import numpy as np


class BaseGenerator(ABC):

    def __init__(self, data):
        self.data = np.asarray(data)

        if self.data.ndim != 1:
            raise ValueError("Data must be one-dimensional")

        if len(self.data) == 0:
            raise ValueError("Data must not be empty")

    @abstractmethod
    def generate(self, n: int, random_state=None) -> np.ndarray:
        pass