import unittest
from unittest.mock import Mock, patch

from housefire.dependency.housefire_client.client import HousefireClient
from housefire.dependency.housefire_client.housefire_object import (
    Geocode,
    Property,
    Reit,
)


class TestHousefireClient(unittest.TestCase):

    def setUp(self):
        self.client = HousefireClient("api-key", "https://example.com/api/")

    def get_response(self, status_code, payload):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = payload
        return response

    def get_property(self, address_input, property_id=None):
        return Property(
            address_input=address_input,
            reit_ticker="PLD",
            id=property_id,
        )

    def test_construct_url_handles_leading_slash(self):
        self.assertEqual(
            self.client._construct_url("/properties"),
            "https://example.com/api/properties",
        )
        self.assertEqual(
            self.client._construct_url("properties"),
            "https://example.com/api/properties",
        )

    @patch("housefire.dependency.housefire_client.client.r.get")
    def test_get_sends_headers_and_params(self, get):
        response = self.get_response(200, [])
        get.return_value = response

        result = self.client._get("/properties", {"limit": 2})

        self.assertIs(result, response)
        get.assert_called_once_with(
            "https://example.com/api/properties",
            headers=self.client.headers,
            params={"limit": 2},
        )

    @patch("housefire.dependency.housefire_client.client.r.post")
    def test_post_sends_json_payload(self, post):
        response = self.get_response(200, {})
        post.return_value = response

        result = self.client._post("/properties", {"name": "Warehouse"})

        self.assertIs(result, response)
        post.assert_called_once_with(
            "https://example.com/api/properties",
            headers=self.client.headers,
            json={"name": "Warehouse"},
        )

    @patch("housefire.dependency.housefire_client.client.r.delete")
    def test_delete_sends_headers(self, delete):
        response = self.get_response(204, None)
        delete.return_value = response

        result = self.client._delete("/properties/1")

        self.assertIs(result, response)
        delete.assert_called_once_with(
            "https://example.com/api/properties/1",
            headers=self.client.headers,
        )

    def test_get_properties_returns_objects(self):
        response = self.get_response(
            200,
            [
                {"addressInput": "1 Main Street", "reitTicker": "PLD"},
                {"addressInput": "2 Main Street", "reitTicker": "PLD"},
            ],
        )
        with patch.object(self.client, "_get", return_value=response) as get:
            properties = self.client.get_properties_by_ticker("PLD")

        get.assert_called_once_with("/properties/byTicker/PLD")
        self.assertEqual(
            [p.address_input for p in properties], ["1 Main Street", "2 Main Street"]
        )

    def test_get_reits_returns_objects(self):
        response = self.get_response(200, [{"ticker": "PLD"}, {"ticker": "DLR"}])
        with patch.object(self.client, "_get", return_value=response) as get:
            reits = self.client.get_reits()
        get.assert_called_once_with("/reits")
        self.assertEqual([reit.ticker for reit in reits], ["PLD", "DLR"])

    def test_post_reit_sends_ticker_and_returns_object(self):
        reit = Reit(ticker="PLD")
        response = self.get_response(200, {"id": "reit-1", "ticker": "PLD"})
        with patch.object(self.client, "_post", return_value=response) as post:
            result = self.client.post_reit(reit)
        post.assert_called_once_with("/reits", {"ticker": "PLD"})
        self.assertEqual(result.ticker, "PLD")

    def test_get_properties_returns_empty_list_for_not_found(self):
        response = self.get_response(404, None)
        with patch.object(self.client, "_get", return_value=response):
            properties = self.client.get_properties_by_ticker("PLD")

        self.assertEqual(properties, [])

    def test_get_properties_raises_for_other_error(self):
        response = self.get_response(500, {"error": "server"})
        with patch.object(self.client, "_get", return_value=response):
            with self.assertRaises(Exception):
                self.client.get_properties_by_ticker("PLD")

    def test_post_properties_rejects_empty_data(self):
        with self.assertRaises(Exception):
            self.client.post_properties([])
        with self.assertRaises(Exception):
            self.client.post_properties(None)

    def test_post_properties_sends_dicts_and_returns_objects(self):
        property_object = self.get_property("1 Main Street")
        response = self.get_response(
            201,
            [{"addressInput": "1 Main Street", "reitTicker": "PLD"}],
        )
        with patch.object(self.client, "_post", return_value=response) as post:
            properties = self.client.post_properties([property_object])

        post.assert_called_once_with("/properties", [property_object.to_dict()])
        self.assertEqual(properties[0].address_input, "1 Main Street")

    def test_post_properties_sends_facts_in_json_payload(self):
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            facts=[{"label": "Year built", "value": "2022"}],
        )
        response = self.get_response(
            201,
            [
                {
                    "addressInput": "1 Main Street",
                    "reitTicker": "PLD",
                    "facts": [{"label": "Year built", "value": "2022"}],
                }
            ],
        )
        with patch.object(self.client, "_post", return_value=response) as post:
            properties = self.client.post_properties([property_object])

        post.assert_called_once_with(
            "/properties",
            [
                {
                    "addressInput": "1 Main Street",
                    "reitTicker": "PLD",
                    "facts": [{"label": "Year built", "value": "2022"}],
                }
            ],
        )
        self.assertEqual(
            properties[0].facts, [{"label": "Year built", "value": "2022"}]
        )

    def test_post_properties_raises_value_error_for_validation_error(self):
        response = self.get_response(400, {"error": "invalid"})
        with patch.object(self.client, "_post", return_value=response):
            with self.assertRaises(ValueError):
                self.client.post_properties([self.get_property("1 Main Street")])

    def test_delete_properties_returns_count(self):
        response = self.get_response(200, {"count": 2})
        with patch.object(self.client, "_delete", return_value=response) as delete:
            count = self.client.delete_properties_by_ticker("PLD")

        delete.assert_called_once_with("/properties/byTicker/PLD")
        self.assertEqual(count, 2)

    def test_get_geocode_returns_none_for_not_found(self):
        response = self.get_response(404, None)
        with patch.object(self.client, "_get", return_value=response):
            geocode = self.client.get_geocode_by_address_input("1 Main Street")

        self.assertIsNone(geocode)

    def test_post_geocode_returns_object(self):
        geocode = Geocode("1 Main Street", 40.0, -73.0)
        response = self.get_response(
            201,
            {"addressInput": "1 Main Street", "latitude": 40.0, "longitude": -73.0},
        )
        with patch.object(self.client, "_post", return_value=response) as post:
            result = self.client.post_geocode(geocode)

        post.assert_called_once_with("/geocodes", geocode.to_dict())
        self.assertEqual(result, geocode)

    def test_update_properties_creates_new_and_deletes_stale(self):
        existing = [
            self.get_property("1 Main Street", "property-1"),
            self.get_property("2 Main Street", "property-2"),
        ]
        new = [self.get_property("1 Main Street"), self.get_property("3 Main Street")]
        created = self.get_property("3 Main Street", "property-3")

        with (
            patch.object(
                self.client, "get_properties_by_ticker", return_value=existing
            ),
            patch.object(self.client, "delete_property_by_id") as delete,
            patch.object(
                self.client, "post_properties", return_value=[created]
            ) as post,
            patch("housefire.dependency.housefire_client.client.time.sleep") as sleep,
        ):
            result = self.client.update_properties_by_ticker("PLD", new)

        delete.assert_called_once_with("property-2")
        post.assert_called_once_with([new[1]])
        sleep.assert_called_once_with(1)
        self.assertEqual(result, [created])

    def test_update_properties_returns_empty_when_everything_exists(self):
        existing = [self.get_property("1 Main Street", "property-1")]
        new = [self.get_property("1 Main Street")]

        with (
            patch.object(
                self.client, "get_properties_by_ticker", return_value=existing
            ),
            patch.object(self.client, "post_properties") as post,
        ):
            result = self.client.update_properties_by_ticker("PLD", new)

        post.assert_not_called()
        self.assertEqual(result, [])

    def test_update_properties_rejects_existing_stale_property_without_id(self):
        existing = [self.get_property("1 Main Street")]
        new = [self.get_property("2 Main Street")]

        with patch.object(
            self.client, "get_properties_by_ticker", return_value=existing
        ):
            with self.assertRaises(Exception):
                self.client.update_properties_by_ticker("PLD", new)


if __name__ == "__main__":
    unittest.main()
