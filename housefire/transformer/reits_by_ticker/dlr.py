from housefire.transformer.transformer import TransformResult
from housefire.scraper.scraper import ScrapeResult
from housefire.transformer.geocode_transformer import GeocodeTransformer


class DlrTransformer(GeocodeTransformer):
    def __init__(self):
        super().__init__()

    def execute_transform(self, data: list[ScrapeResult]) -> list[TransformResult]:
        results_with_geocode = self._geocode_transform(data)
        for result in results_with_geocode:
            result.property.square_footage = self.parse_area_string(
                result.scrape_result.property_info["square_footage"]
            )
        return results_with_geocode
