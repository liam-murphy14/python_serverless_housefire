import unittest
from unittest.mock import Mock, patch

from housefire.dependency.google_maps import GoogleGeocodeAPI
from housefire.dependency.housefire_client.housefire_object import Geocode


class TestGoogleGeocodeAPI(unittest.TestCase):

    def get_google_response(self):
        return {
            "address_components": [
                {"long_name": "1", "types": ["street_number"]},
                {"long_name": "Main Street", "types": ["route"]},
                {"long_name": "Midtown", "types": ["locality"]},
                {"long_name": "New York", "types": ["administrative_area_level_2"]},
                {"long_name": "New York", "types": ["administrative_area_level_1"]},
                {"long_name": "United States", "types": ["country"]},
                {"long_name": "10001", "types": ["postal_code"]},
            ],
            "formatted_address": "1 Main Street, New York, NY 10001, USA",
            "plus_code": {"global_code": "87G8Q2X2+2X"},
            "geometry": {"location": {"lat": 40.0, "lng": -73.0}},
        }

    def get_api(self, housefire_client=None):
        with patch("housefire.dependency.google_maps.googlemaps.Client") as client:
            api = GoogleGeocodeAPI(Mock(), housefire_client or Mock(), "google-key")
        return api, client

    def test_constructor_creates_google_client(self):
        api, client = self.get_api()

        client.assert_called_once_with(key="google-key")
        self.assertEqual(api.wait_time, 72)

    def test_google_response_is_converted_to_geocode(self):
        api, _ = self.get_api()

        geocode = api._google_geocode_to_housefire_geocode(
            self.get_google_response(), "1 Main Street"
        )

        self.assertEqual(
            geocode,
            Geocode(
                address_input="1 Main Street",
                latitude=40.0,
                longitude=-73.0,
                street_number="1",
                route="Main Street",
                locality="Midtown",
                administrative_area_level1="New York",
                administrative_area_level2="New York",
                country="United States",
                postal_code="10001",
                formatted_address="1 Main Street, New York, NY 10001, USA",
                global_plus_code="87G8Q2X2+2X",
            ),
        )

    def test_google_response_allows_missing_optional_fields(self):
        api, _ = self.get_api()
        response = self.get_google_response()
        del response["formatted_address"]
        del response["plus_code"]

        geocode = api._google_geocode_to_housefire_geocode(response, "1 Main Street")

        self.assertIsNone(geocode.formatted_address)
        self.assertIsNone(geocode.global_plus_code)

    @patch("housefire.dependency.google_maps.time.sleep")
    def test_geocode_addresses_uses_cached_results(self, sleep):
        housefire_client = Mock()
        cached = Geocode("1 Main Street", 40.0, -73.0)
        housefire_client.get_geocode_by_address_input.return_value = cached
        api, _ = self.get_api(housefire_client)

        results = api.geocode_addresses(["1 Main Street"])

        self.assertEqual(results, {"1 Main Street": cached})
        api.client.geocode.assert_not_called()
        sleep.assert_called_once_with(5)

    @patch("housefire.dependency.google_maps.time.sleep")
    def test_geocode_addresses_posts_google_result_and_skips_empty_result(self, sleep):
        housefire_client = Mock()
        housefire_client.get_geocode_by_address_input.return_value = None
        posted = Geocode("1 Main Street", 40.0, -73.0)
        housefire_client.post_geocode.return_value = posted
        api, _ = self.get_api(housefire_client)
        api.client.geocode.side_effect = [[self.get_google_response()], []]
        api.wait_time = 3

        results = api.geocode_addresses(["1 Main Street", "Unknown Street"])

        self.assertEqual(results, {"1 Main Street": posted})
        housefire_client.post_geocode.assert_called_once()
        sleep.assert_called_once_with(3)
        self.assertEqual(api.client.geocode.call_count, 2)


if __name__ == "__main__":
    unittest.main()
