import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from housefire.dependency.housefire_client.housefire_object import Geocode, Property
from housefire.scraper.scraper import ScrapeResult
from housefire.transformer.geocode_transformer import GeocodeTransformer
from housefire.transformer.reits_by_ticker.dlr import DlrTransformer
from housefire.transformer.reits_by_ticker.pld import PldTransformer
from housefire.transformer.transformer import TransformResult, Transformer


class FakeTransformer(Transformer):

    def __init__(self, transform_results=None):
        super().__init__()
        self.transform_results = transform_results or []
        self.received_data = None

    def execute_transform(self, data):
        self.received_data = data
        return self.transform_results


class TestTransformer(unittest.TestCase):

    def get_transform_result(self, address_input, reit_ticker="pld"):
        property_object = Property(
            address_input=address_input,
            reit_ticker=reit_ticker,
        )
        return TransformResult(
            property=property_object,
            scrape_result=ScrapeResult({"address_input": address_input}),
        )

    def test_transform_uppercases_ticker_and_drops_duplicate_addresses(self):
        first = self.get_transform_result("1 Main Street")
        duplicate = self.get_transform_result("1 Main Street")
        second = self.get_transform_result("2 Main Street")
        transformer = FakeTransformer([first, duplicate, second])
        transformer.ticker = "pld"
        transformer.logger = Mock()

        results = transformer.transform([])

        self.assertEqual(results, [first, second])
        self.assertEqual(first.property.reit_ticker, "PLD")
        self.assertEqual(second.property.reit_ticker, "PLD")
        transformer.logger.debug.assert_called()

    def test_debug_transform_limits_input_to_five_results(self):
        data = [ScrapeResult({"address_input": str(index)}) for index in range(7)]
        transformer = FakeTransformer(
            [self.get_transform_result(str(index)) for index in range(5)]
        )
        transformer.ticker = "pld"
        transformer.logger = Mock()

        transformer._debug_transform(data)

        self.assertEqual(transformer.received_data, data[:5])

    def test_parse_area_unit_supports_acres_and_square_feet(self):
        self.assertEqual(transformer_parse_area_unit("10 AC"), "acres")
        self.assertEqual(transformer_parse_area_unit("10,000 SF"), "sqft")
        self.assertEqual(transformer_parse_area_unit("10 ft"), "sqft")

    def test_parse_area_unit_rejects_unknown_units(self):
        with self.assertRaises(ValueError):
            transformer_parse_area_unit("10 hectares")

    def test_parse_area_range_averages_two_values(self):
        self.assertEqual(Transformer.parse_area_range("1,000-3,000 sf"), 2000.0)
        self.assertEqual(Transformer.parse_area_range("1,000 sf"), 1000.0)

    def test_parse_area_range_rejects_more_than_two_values(self):
        with self.assertRaises(ValueError):
            Transformer.parse_area_range("1-2-3 sf")

    def test_parse_and_convert_area_converts_acres_to_square_feet(self):
        self.assertEqual(Transformer.parse_and_convert_area("2 ac"), 87120.0)
        self.assertEqual(Transformer.parse_and_convert_area("1,500 sf"), 1500.0)

    def test_parse_area_string_removes_non_digits(self):
        self.assertEqual(Transformer.parse_area_string("12,500 SF"), 12500.0)

    def test_transform_result_can_write_and_read_property_csv(self):
        result = self.get_transform_result("1 Main Street")
        result.property.name = "Warehouse"

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "properties.csv"
            TransformResult.to_csv([result], path)
            properties = TransformResult.from_csv(path)

        self.assertEqual(len(properties), 1)
        self.assertEqual(properties[0].property.address_input, "1 Main Street")
        self.assertEqual(properties[0].property.name, "Warehouse")
        self.assertEqual(properties[0].scrape_result.property_info, {})


def transformer_parse_area_unit(area):
    return Transformer.parse_area_unit(area)


class TestPldTransformer(unittest.TestCase):

    def test_execute_transform_maps_fields_and_converts_area(self):
        transformer = PldTransformer()
        transformer.ticker = "pld"
        result = ScrapeResult(
            {
                "Property Name": "Distribution Center",
                "Street Address 1": "1 Main Street",
                "Street Address 2": "Suite 2",
                "Neighborhood": "Midtown",
                "City": "New York",
                "State": "NY",
                "Postal Code": "10001",
                "Country": "US",
                "Latitude": "40.0",
                "Longitude": "-73.0",
                "Available Square Footage": "2 ac",
            }
        )

        transformed = transformer.execute_transform([result])

        property_object = transformed[0].property
        self.assertEqual(property_object.name, "Distribution Center")
        self.assertEqual(property_object.address2, "Suite 2")
        self.assertEqual(property_object.latitude, 40.0)
        self.assertEqual(property_object.longitude, -73.0)
        self.assertEqual(property_object.square_footage, 87120.0)
        self.assertEqual(
            property_object.address_input,
            "1 Main Street, New York, NY 10001, US",
        )


class TestGeocodeTransformer(unittest.TestCase):

    def test_geocode_transform_filters_missing_and_failed_addresses(self):
        transformer = DlrTransformer()
        transformer.ticker = "spg"
        transformer.logger = Mock()
        transformer.google_geocode_api_client = Mock()
        geocode = Geocode(
            address_input="1 Main Street",
            latitude=40.0,
            longitude=-73.0,
            street_number="1",
            route="Main Street",
            locality="Midtown",
            administrative_area_level1="NY",
            administrative_area_level2="New York",
            country="US",
            postal_code="10001",
        )
        transformer.google_geocode_api_client.geocode_addresses.return_value = {
            "1 Main Street": geocode
        }
        data = [
            ScrapeResult({"address_input": "1 Main Street", "square_footage": "100"}),
            ScrapeResult({"address_input": "Unknown Street"}),
            ScrapeResult({"name": "Missing address"}),
        ]

        transformed = transformer.transform(data)

        transformer.google_geocode_api_client.geocode_addresses.assert_called_once_with(
            ["1 Main Street", "Unknown Street"]
        )
        self.assertEqual(len(transformed), 1)
        property_object = transformed[0].property
        self.assertEqual(property_object.reit_ticker, "SPG")
        self.assertEqual(property_object.address, "1 Main Street")
        self.assertEqual(property_object.city, "New York")
        self.assertEqual(property_object.state, "NY")
        self.assertEqual(property_object.zip, "10001")
        self.assertEqual(property_object.latitude, 40.0)
        self.assertEqual(property_object.longitude, -73.0)

    def test_add_geocode_to_property_maps_address_fields(self):
        property_object = Property("1 Main Street", "SPG")
        geocode = Geocode(
            address_input="1 Main Street",
            latitude=40.0,
            longitude=-73.0,
            street_number="1",
            route="Main Street",
            locality="Midtown",
            administrative_area_level1="NY",
            administrative_area_level2="New York",
            country="US",
            postal_code="10001",
        )

        GeocodeTransformer._add_geocode_to_property(property_object, geocode)

        self.assertEqual(property_object.address, "1 Main Street")
        self.assertEqual(property_object.neighborhood, "Midtown")
        self.assertEqual(property_object.city, "New York")
        self.assertEqual(property_object.country, "US")


class TestDlrTransformer(unittest.TestCase):

    def test_execute_transform_sets_square_footage(self):
        transformer = DlrTransformer()
        transformer.ticker = "dlr"
        transformer.logger = Mock()
        transformer.google_geocode_api_client = Mock()
        transformer.google_geocode_api_client.geocode_addresses.return_value = {
            "1 Main Street": Geocode("1 Main Street", 40.0, -73.0)
        }
        result = ScrapeResult(
            {"address_input": "1 Main Street", "square_footage": "12,500 SF"}
        )

        transformed = transformer.transform([result])

        self.assertEqual(transformed[0].property.square_footage, 12500.0)
        self.assertEqual(transformed[0].property.reit_ticker, "DLR")


if __name__ == "__main__":
    unittest.main()
