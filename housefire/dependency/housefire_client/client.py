import requests as r
import time
from housefire.dependency.housefire_client.housefire_object import Property, Geocode


class HousefireClient:
    """
    Housefire API client

    Args:
        api_key (str): Housefire API key
    """

    def __init__(
        self,
        housefire_api_key: str,
        housefire_base_url: str = "https://housefire.liammurphydev.com/api/",
    ):
        self.base_url = housefire_base_url
        self.headers = {
            "x-api-key": housefire_api_key,
            "Content-Type": "application/json",
        }

    def _construct_url(self, endpoint: str):
        full_url = self.base_url + endpoint
        if endpoint.startswith("/") and len(endpoint) > 1:
            full_url = self.base_url + endpoint[1:]
        return full_url

    def _get(self, endpoint: str, params=None) -> r.Response:
        response = r.get(
            self._construct_url(endpoint), headers=self.headers, params=params
        )
        return response

    def _post(self, endpoint: str, data=None) -> r.Response:
        response = r.post(
            self._construct_url(endpoint), headers=self.headers, json=data
        )
        return response

    def _delete(self, endpoint: str) -> r.Response:
        response = r.delete(self._construct_url(endpoint), headers=self.headers)
        return response

    def get_properties_by_ticker(self, ticker: str) -> list[Property]:
        """
        gets all properties for a given ticker, returning an empty list if no properties are found,
        and raising an exception if an unexpected error occurs
        """
        r = self._get(f"/properties/byTicker/{ticker}")
        if r.status_code == 404:
            return list()
        elif self._is_error_response(r):
            raise Exception(
                f"unexpected error getting properties for ticker {ticker}: {r}"
            )
        return list(
            map(lambda prop_dict: Property.from_dict(prop_dict), list(r.json()))
        )

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

    def post_properties(self, data: list[Property]) -> list[Property]:
        """
        creates many properties, returning a list of the created properties,
        raising an exception in the case of a validation error, or any other unexpected error
        """
        if data is None or len(data) == 0:
            raise Exception("data must be a non-empty list of Property objects")
        r = self._post(f"/properties", list(map(lambda prop: prop.to_dict(), data)))
        if r.status_code == 400:
            raise ValueError(f"validation error while creating properties: {r}")
        elif self._is_error_response(r):
            raise Exception(f"unexpected error creating properties: {r}")
        return list(
            map(lambda prop_dict: Property.from_dict(prop_dict), list(r.json()))
        )

    def update_properties_by_ticker(
        self, ticker: str, data: list[Property]
    ) -> list[Property]:
        """
        updates many properties for a given ticker, returning a list of the updated properties,
        raising an exception in the case of a validation error, or any other unexpected error
        """
        if data is None or len(data) == 0:
            raise Exception("data must be a non-empty list of property objects")
        existing_properties = self.get_properties_by_ticker(ticker)
        existing_property_dict_by_addressInput = {
            p.address_input: p for p in existing_properties
        }
        new_property_address_input_set = {p.address_input for p in data}

        to_create: list[Property] = list()
        for new_property in data:
            if new_property.address_input in existing_property_dict_by_addressInput:
                continue
            to_create.append(new_property)
        for existing_property in existing_properties:
            if existing_property.address_input in new_property_address_input_set:
                continue
            if existing_property.id is None:
                raise Exception(
                    f"existing property {existing_property.address_input} has no ID"
                )
            self.delete_property_by_id(existing_property.id)
            time.sleep(1)
        return self.post_properties(to_create) if len(to_create) > 0 else list()

    def get_geocode_by_address_input(self, address_input: str) -> Geocode | None:
        """
        gets a geocode by address input, returning the geocode as a dict if it exists, and None if it does not,
        and raising an exception if an unexpected error occurs
        """
        r = self._get(f"/geocodes/byAddressInput/{address_input}")
        if r.status_code == 404:
            return None
        elif self._is_error_response(r):
            raise Exception(
                f"unexpected error getting geocode for address input {address_input}: {r}"
            )
        return Geocode.from_dict(r.json())

    def post_geocode(self, data: Geocode) -> Geocode:
        """
        creates a geocode, returning the created geocode, raising an exception in the case of a validation error,
        or any other unexpected error
        """
        r = self._post(f"/geocodes", data.to_dict())
        if r.status_code == 400:
            raise ValueError(f"validation error while creating geocode: {r}")
        elif self._is_error_response(r):
            raise Exception(f"unexpected error creating geocode: {r}")
        return Geocode.from_dict(r.json())

    @staticmethod
    def _is_error_response(response: r.Response) -> bool:
        return response.status_code >= 400
