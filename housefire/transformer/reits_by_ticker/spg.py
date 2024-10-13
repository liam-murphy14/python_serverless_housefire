
import pandas as pd
from housefire.transformer.geocode_transformer import GeocodeTransformer

class SpgTransformer(GeocodeTransformer):
    def __init__(self):
        super().__init__()
        self.ticker = "spg"

    def execute_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._geocode_transform(data)