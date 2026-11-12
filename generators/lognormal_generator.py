import numpy as np
from scipy import stats
from generators.base_generator import BaseGenerator

class LogNormalGenerator(BaseGenerator):
    def __init__(self, data):
        super().__init__(data)
        
        valid_data = self.data[self.data > 0]
        mu = np.mean(np.log(valid_data))
        sigma = np.std(np.log(valid_data))
        
        self.shape = sigma
        self.loc = 0
        self.scale = np.exp(mu)

    def generate(self, n: int, random_state=None) -> np.ndarray:
        return stats.lognorm.rvs(s=self.shape, loc=self.loc, scale=self.scale, size=n, random_state=random_state)
