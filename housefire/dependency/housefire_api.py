import requests as r
import time
import housefire.config as config
from housefire.logger import get_logger
from housefire.dependency.dependency import Dependency

logger = get_logger(__name__)

class HousefireAPI(Dependency):
    """
    Housefire API client

    Args:
        api_key (str): Housefire API key
    """

    def __init__(
        self, base_url: str = config.HOUSEFIRE_DEFAULT_BASE_URL
    ):
        self.base_url = base_url
        self.headers = {
            "x-api-key": config.HOUSEFIRE_API_KEY,
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
        elif self._is_error_response(r):
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
        if self._is_error_response(r):
            raise Exception(
                f"unexpected error deleting properties for ticker {ticker}: {r}"
            )
        return r.json()["count"]

    def delete_property_by_id(self, property_id: str):
        """
        deletes a property by ID, raising an exception if an unexpected error occurs
        """
        r = self._delete(f"/properties/{property_id}")
        if self._is_error_response(r):
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
        elif self._is_error_response(r):
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
        elif self._is_error_response(r):
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
        elif self._is_error_response(r):
            raise Exception(f"unexpected error creating geocode: {r}")
        return r.json()


    @staticmethod
    def housefire_geocode_to_housefire_address(housefire_geocode: dict) -> dict:
        return {
            "addressInput": housefire_geocode["addressInput"],
            "address": f"{housefire_geocode['streetNumber']} {housefire_geocode['route']}",
            "neighborhood": housefire_geocode["locality"],
            "city": housefire_geocode["administrativeAreaLevel2"],
            "state": housefire_geocode["administrativeAreaLevel1"],
            "zip": housefire_geocode["postalCode"],
            "country": housefire_geocode["country"],
            "latitude": housefire_geocode["latitude"],
            "longitude": housefire_geocode["longitude"],
        }

