import numpy as np
from scipy import stats
from generators.base_generator import BaseGenerator

class LogNormalGenerator(BaseGenerator):
    def __init__(self):
        self.shape = None
        self.loc = None
        self.scale = None

    def fit(self, data):
        valid_data = data[data > 0]
        mu = np.mean(np.log(valid_data))
        sigma = np.std(np.log(valid_data))
        
        self.shape = sigma
        self.loc = 0
        self.scale = np.exp(mu)

    def generate(self, size=1):
        if self.shape is None:
            raise ValueError("Сначала нужно передать данные через метод fit()")
        return stats.lognorm.rvs(s=self.shape, loc=self.loc, scale=self.scale, size=size)