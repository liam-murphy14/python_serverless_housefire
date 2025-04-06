from housefire.transformer.transformer import TransformResult
from housefire.scraper.scraper import ScrapeResult
from housefire.transformer.geocode_transformer import GeocodeTransformer


class WellTransformer(GeocodeTransformer):
    def __init__(self):
        super().__init__()

    def execute_transform(self, data: list[ScrapeResult]) -> list[TransformResult]:
        return self._geocode_transform(data)
