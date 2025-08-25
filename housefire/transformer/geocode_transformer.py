from housefire.dependency.google_maps import GoogleGeocodeAPI
from housefire.dependency.housefire_client.housefire_object import Property, Geocode
from housefire.transformer.transformer import Transformer, TransformResult
from housefire.scraper.scraper import ScrapeResult


class GeocodeTransformer(Transformer):
    """
    Transformer that geocodes addresses during the transformation process.
    """

    # instantiated by factory
    google_geocode_api_client: GoogleGeocodeAPI

    def __init__(self):
        super().__init__()

    def _geocode_transform(self, data: list[ScrapeResult]) -> list[TransformResult]:
        """
        geocodes addresses in dataframe by calling housefire api to get geocode for each df["address"] entry,
        calling google geocode api if housefire api does not have the geocode and saving the result in housefire,
        then populating the dataframe fields with the geocode data
        """

        housefire_geocode_map = self.google_geocode_api_client.geocode_addresses(
            list(
                map(
                    lambda x: x.property_info["address_input"],
                    filter(lambda x: "address_input" in x.property_info, data),
                )
            )
        )

        results: list[TransformResult] = list()
        for result in data:
            address_input = (
                result.property_info["address_input"]
                if "address_input" in result.property_info
                else None
            )
            if address_input is None:
                self.logger.error("No address input found in property info")
                continue
            if address_input not in housefire_geocode_map:
                self.logger.error(f"Failed to geocode address: {address_input}")
                continue

            property = Property(address_input=address_input, reit_ticker=self.ticker)
            housefire_geocode = housefire_geocode_map[address_input]
            self._add_geocode_to_property(property, housefire_geocode)
            results.append(TransformResult(property=property, scrape_result=result))
        return results

    @staticmethod
    def _add_geocode_to_property(prop: Property, geocode: Geocode) -> None:
        """
        adds geocode data to property
        """
        prop.address = f"{geocode.street_number} {geocode.route}"
        prop.neighborhood = geocode.locality
        prop.city = geocode.administrative_area_level2
        prop.state = geocode.administrative_area_level1
        prop.zip = geocode.postal_code
        prop.country = geocode.country
        prop.latitude = geocode.latitude
        prop.longitude = geocode.longitude
