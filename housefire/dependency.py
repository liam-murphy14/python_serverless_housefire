import requests as r
import time
from housefire.logger import get_logger
import googlemaps

logger = get_logger(__name__)


def _is_error_response(response: r.Response) -> bool:
    return response.status_code >= 400


class HousefireAPI:
    """
    Housefire API client

    Args:
        api_key (str): Housefire API key
    """

    def __init__(
        self, api_key: str, base_url: str = "https://housefire.liammurphydev.com/api/"
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        logger.debug("Housefire API client initialized")

    def _construct_url(self, endpoint: str):
        full_url = self.base_url + endpoint
        if endpoint.startswith("/") and len(endpoint) > 1:
            full_url = self.base_url + endpoint[1:]
        logger.debug(f"Constructed URL: {full_url}")
        return full_url

    def _get(self, endpoint, params=None) -> r.Response:
        logger.debug(f"GET request to {endpoint} with params: {params}")
        response = r.get(
            self._construct_url(endpoint), headers=self.headers, params=params
        )
        logger.debug(f"GET request to {endpoint} returned: {response}")
        return response

    def _post(self, endpoint, data=None) -> r.Response:
        logger.debug(f"POST request to {endpoint} with data: {data}")
        response = r.post(
            self._construct_url(endpoint), headers=self.headers, json=data
        )
        logger.debug(f"POST request to {endpoint} returned: {response}")
        return response

    def _delete(self, endpoint) -> r.Response:
        logger.debug(f"DELETE request to {endpoint}")
        response = r.delete(self._construct_url(endpoint), headers=self.headers)
        logger.debug(f"DELETE request to {endpoint} returned: {response}")
        return response

    def get_properties_by_ticker(self, ticker: str) -> list[dict]:
        """
        gets all properties for a given ticker, returning an empty list if no properties are found,
        and raising an exception if an unexpected error occurs
        """
        r = self._get(f"/properties/byTicker/{ticker}")
        if r.status_code == 404:
            logger.debug(f"no properties found for ticker {ticker}")
            return list()
        elif _is_error_response(r):
            raise Exception(
                f"unexpected error getting properties for ticker {ticker}: {r}"
            )
        logger.debug(f"properties found for ticker {ticker}: {r.json()}")
        return list(r.json())

    def delete_properties_by_ticker(self, ticker: str) -> int:
        """
        deletes all properties for a given ticker, returning the number of properties deleted,
        and raising an exception if an unexpected error occurs
        """
        r = self._delete(f"/properties/byTicker/{ticker}")
        if _is_error_response(r):
            raise Exception(
                f"unexpected error deleting properties for ticker {ticker}: {r}"
            )
        return r.json()["count"]

    def delete_property_by_id(self, property_id: str):
        """
        deletes a property by ID, raising an exception if an unexpected error occurs
        """
        r = self._delete(f"/properties/{property_id}")
        if _is_error_response(r):
            raise Exception(f"unexpected error deleting property {property_id}: {r}")

    def post_properties(self, data: list[dict]) -> list[dict]:
        """
        creates many properties, returning a list of the created properties,
        raising an exception in the case of a validation error, or any other unexpected error
        """
        if data is None or len(data) == 0:
            raise Exception("data must be a non-empty list of property objects")
        r = self._post(f"/properties", data)
        if r.status_code == 400:
            raise ValueError(f"validation error while creating properties: {r}")
        elif _is_error_response(r):
            raise Exception(f"unexpected error creating properties: {r}")
        return list(r.json())

    def update_properties_by_ticker(self, ticker: str, data: list[dict]) -> list[dict]:
        """
        updates many properties for a given ticker, returning a list of the updated properties,
        raising an exception in the case of a validation error, or any other unexpected error
        """
        if data is None or len(data) == 0:
            raise Exception("data must be a non-empty list of property objects")
        existing_properties = self.get_properties_by_ticker(ticker)
        existing_property_dict_by_addressInput = {
            p["addressInput"]: p for p in existing_properties
        }
        new_property_address_input_set = {p["addressInput"] for p in data}

        to_create = list()
        for new_property in data:
            if new_property["addressInput"] in existing_property_dict_by_addressInput:
                continue
            to_create.append(new_property)
        for existing_property in existing_properties:
            if existing_property["addressInput"] in new_property_address_input_set:
                continue
            self.delete_property_by_id(existing_property["id"])
            time.sleep(1)
        return self.post_properties(to_create) if len(to_create) > 0 else list()

    def get_geocode_by_address_input(self, address_input: str) -> dict | None:
        """
        gets a geocode by address input, returning the geocode as a dict if it exists, and None if it does not,
        and raising an exception if an unexpected error occurs
        """
        r = self._get(f"/geocodes/byAddressInput/{address_input}")
        if r.status_code == 404:
            logger.debug(f"no geocode found for address input {address_input}")
            return None
        elif _is_error_response(r):
            raise Exception(
                f"unexpected error getting geocode for address input {address_input}: {r}"
            )
        logger.debug(f"geocode found for address input {address_input}: {r.json()}")
        return r.json()

    def post_geocode(self, data: dict) -> dict:
        """
        creates a geocode, returning the geocode as a dict, raising an exception in the case of a validation error,
        or any other unexpected error
        """
        r = self._post(f"/geocodes", data)
        if r.status_code == 400:
            raise ValueError(f"validation error while creating geocode: {r}")
        elif _is_error_response(r):
            raise Exception(f"unexpected error creating geocode: {r}")
        return r.json()


class GoogleGeocodeAPI:

    def __init__(self, api_key: str, housefire_api_client: HousefireAPI):
        self.api_key = api_key
        self.client = googlemaps.Client(key=api_key)
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
                time.sleep(1)  # hacky rate limit
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


if __name__ == "__main__":
    import pandas as pd
    from housefire.utils import parse_area_string, get_env_nonnull
    import dotenv

    dotenv.load_dotenv()

    df = pd.DataFrame(
        {
            "name": ["Chicago CH2"],
            "address": ["2200 Busse Road, Elk Grove Village, IL 60007"],
            "squareFootage": ["485,000"],
        }
    )

    df["squareFootage"] = df["squareFootage"].apply(parse_area_string)
    address_inputs = df["address"].to_list()
    df.drop(columns=["address"], inplace=True)
    records = df.to_dict(orient="records")
    housefire_api_client = HousefireAPI(get_env_nonnull("HOUSEFIRE_API_KEY"))
    google_geocode_api_client = GoogleGeocodeAPI(
        get_env_nonnull("GOOGLE_MAPS_API_KEY"), housefire_api_client
    )
    housefire_geocodes = google_geocode_api_client.geocode_addresses(address_inputs)
