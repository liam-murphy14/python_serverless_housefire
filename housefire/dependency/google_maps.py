import googlemaps
import housefire.config as config
from housefire.dependency.housefire_api import HousefireAPI
from housefire.dependency.dependency import Dependency
from housefire.logger import get_logger
import time

logger = get_logger(__name__)

class GoogleGeocodeAPI(Dependency):

    def __init__(self, housefire_api_client: HousefireAPI):
        self.client = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)
        self.housefire_api_client = housefire_api_client
        self.wait_time = 72  # wait 72 seconds between geocoding requests to limit to 1200 requests per day

    def geocode_addresses(self, address_inputs: list[str]) -> dict[str, dict]:
        """
        geocodes a list of addresses and returns a dictionary of address inputs to housefire geocode results
        """
        results = dict()
        for address_input in address_inputs:
            housefire_geocode = self.housefire_api_client.get_geocode_by_address_input(
                address_input
            )
            if housefire_geocode is not None:
                logger.debug(f"address input {address_input} already in housefire")
                results[address_input] = housefire_geocode
                time.sleep(5)  # hacky rate limit
                continue
            logger.debug(f"geocoding address input with google: {address_input}")
            google_geocode_response = self.client.geocode(address_input)
            logger.debug(
                f"geocoded address input {address_input} with response: {google_geocode_response}"
            )
            if len(google_geocode_response) == 0:
                logger.error(f"no results found for address input {address_input}")
                continue

            housefire_geocode = self._google_geocode_to_housefire_geocode(
                google_geocode_response[0]
            )
            logger.debug(
                f"converted google geocode to housefire geocode: {housefire_geocode}"
            )
            housefire_geocode["addressInput"] = address_input
            housefire_geocode_response_data = self.housefire_api_client.post_geocode(
                housefire_geocode
            )
            results[address_input] = housefire_geocode_response_data
            time.sleep(self.wait_time)  # hacky rate limit for google
        return results

    def _google_geocode_to_housefire_geocode(self, google_geocode: dict) -> dict:
        (
            street_number,
            route,
            locality,
            administrative_area_level_1,
            administrative_area_level_2,
            country,
            postal_code,
        ) = (None, None, None, None, None, None, None)
        for component in google_geocode["address_components"]:
            for component_type in component["types"]:
                if component_type == "street_number":
                    street_number = component["long_name"]
                elif component_type == "route":
                    route = component["long_name"]
                elif component_type == "locality":
                    locality = component["long_name"]
                elif component_type == "administrative_area_level_1":
                    administrative_area_level_1 = component["long_name"]
                elif component_type == "administrative_area_level_2":
                    administrative_area_level_2 = component["long_name"]
                elif component_type == "country":
                    country = component["long_name"]
                elif component_type == "postal_code":
                    postal_code = component["long_name"]

        return {
            "streetNumber": street_number,
            "route": route,
            "locality": locality,
            "administrativeAreaLevel1": administrative_area_level_1,
            "administrativeAreaLevel2": administrative_area_level_2,
            "country": country,
            "postalCode": postal_code,
            "formattedAddress": (
                google_geocode["formatted_address"]
                if "formatted_address" in google_geocode
                else None
            ),
            "globalPlusCode": (
                google_geocode["plus_code"]["global_code"]
                if "plus_code" in google_geocode
                else None
            ),
            "latitude": google_geocode["geometry"]["location"][
                "lat"
            ],  # these should never be None, throw error
            "longitude": google_geocode["geometry"]["location"]["lng"],
        }
