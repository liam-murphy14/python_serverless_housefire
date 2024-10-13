import pandas as pd
from housefire.transformer.geocode_transformer import GeocodeTransformer

class DlrTransformer(GeocodeTransformer):
    def __init__(self):
        super().__init__()
        self.ticker = "dlr"

    def execute_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        data["squareFootage"] = data["squareFootage"].apply(self.parse_area_string)
        return self._geocode_transform(data)
