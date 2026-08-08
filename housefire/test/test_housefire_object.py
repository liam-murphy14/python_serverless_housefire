import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from housefire.dependency.housefire_client.housefire_object import (
    Geocode,
    Property,
    Reit,
)


class TestHousefireObject(unittest.TestCase):

    def test_reit_to_dict_omits_api_metadata(self):
        reit = Reit(
            ticker="PLD",
            id="reit-1",
            created_at=datetime.fromisoformat("2026-01-01T00:00:00"),
        )
        self.assertEqual(reit.to_dict(), {"ticker": "PLD"})

    def test_reit_from_dict_reads_api_metadata(self):
        reit = Reit.from_dict(
            {
                "id": "reit-1",
                "createdAt": "2026-01-01T00:00:00",
                "updatedAt": "2026-01-02T00:00:00",
                "ticker": "PLD",
            }
        )
        self.assertEqual(reit.ticker, "PLD")
        self.assertEqual(reit.id, "reit-1")
        self.assertEqual(
            reit.created_at,
            datetime.fromisoformat("2026-01-01T00:00:00"),
        )

    def test_geocode_to_dict_omits_optional_fields_and_metadata(self):
        geocode = Geocode(
            address_input="1 Main Street",
            latitude=40.0,
            longitude=-73.0,
            id="geocode-id",
            created_at=datetime(2024, 1, 1),
        )

        self.assertEqual(
            geocode.to_dict(),
            {
                "addressInput": "1 Main Street",
                "latitude": 40.0,
                "longitude": -73.0,
            },
        )

    def test_geocode_from_dict_converts_dates_and_coordinates(self):
        geocode = Geocode.from_dict(
            {
                "id": "geocode-id",
                "createdAt": "2024-01-02T03:04:05",
                "updatedAt": "2024-01-03T03:04:05",
                "addressInput": "1 Main Street",
                "streetNumber": "1",
                "route": "Main Street",
                "latitude": "40.0",
                "longitude": "-73.0",
            }
        )

        self.assertEqual(geocode.id, "geocode-id")
        self.assertEqual(geocode.created_at, datetime(2024, 1, 2, 3, 4, 5))
        self.assertEqual(geocode.updated_at, datetime(2024, 1, 3, 3, 4, 5))
        self.assertEqual(geocode.latitude, 40.0)
        self.assertEqual(geocode.longitude, -73.0)
        self.assertEqual(geocode.route, "Main Street")

    def test_property_to_dict_omits_none_values_and_metadata(self):
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            id="property-id",
            name="Warehouse",
            city="New York",
            latitude=40.0,
            square_footage=12500.0,
        )

        self.assertEqual(
            property_object.to_dict(),
            {
                "name": "Warehouse",
                "addressInput": "1 Main Street",
                "city": "New York",
                "latitude": 40.0,
                "squareFootage": 12500.0,
                "reitTicker": "PLD",
            },
        )

    def test_property_to_dict_includes_ordered_facts(self):
        facts = [
            {"label": "Year built", "value": "2022"},
            {"label": "Lease term", "value": "15 years"},
        ]
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            facts=facts,
        )

        self.assertEqual(property_object.to_dict()["facts"], facts)

    def test_property_from_dict_reads_facts_and_defaults_when_omitted(self):
        facts = [{"label": "Year built", "value": "2022"}]

        property_with_facts = Property.from_dict(
            {
                "addressInput": "1 Main Street",
                "reitTicker": "PLD",
                "facts": facts,
            }
        )
        property_without_facts = Property.from_dict(
            {
                "addressInput": "2 Main Street",
                "reitTicker": "PLD",
            }
        )

        self.assertEqual(property_with_facts.facts, facts)
        self.assertIsNone(property_without_facts.facts)

    def test_property_csv_round_trip_preserves_ordered_facts(self):
        facts = [
            {"label": "Year built", "value": "2022"},
            {"label": "Lease term", "value": "15 years"},
        ]
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            facts=facts,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "properties.csv"
            Property.to_csv([property_object], path)
            properties = Property.from_csv(path)

        self.assertEqual(properties[0].facts, facts)

    def test_property_from_dict_converts_dates_and_numeric_values(self):
        property_object = Property.from_dict(
            {
                "id": "property-id",
                "createdAt": "2024-01-02T03:04:05",
                "updatedAt": "2024-01-03T03:04:05",
                "name": "Warehouse",
                "addressInput": "1 Main Street",
                "latitude": "40.0",
                "longitude": "-73.0",
                "squareFootage": "12500",
                "reitTicker": "PLD",
            }
        )

        self.assertEqual(property_object.id, "property-id")
        self.assertEqual(property_object.created_at, datetime(2024, 1, 2, 3, 4, 5))
        self.assertEqual(property_object.updated_at, datetime(2024, 1, 3, 3, 4, 5))
        self.assertEqual(property_object.latitude, 40.0)
        self.assertEqual(property_object.longitude, -73.0)
        self.assertEqual(property_object.square_footage, 12500.0)

    def test_geocode_from_csv_reads_required_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "geocodes.csv"
            path.write_text(
                "addressInput,latitude,longitude\n" "1 Main Street,40.0,-73.0\n"
            )

            geocodes = Geocode.from_csv(path)

        self.assertEqual(len(geocodes), 1)
        self.assertEqual(geocodes[0].address_input, "1 Main Street")
        self.assertEqual(geocodes[0].latitude, 40.0)

    def test_geocode_csv_round_trip_handles_blank_metadata(self):
        geocode = Geocode("1 Main Street", 40.0, -73.0)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "geocodes.csv"
            Geocode.to_csv([geocode], path)
            geocodes = Geocode.from_csv(path)

        self.assertEqual(len(geocodes), 1)
        self.assertEqual(geocodes[0].address_input, "1 Main Street")
        self.assertEqual(geocodes[0].latitude, 40.0)
        self.assertEqual(geocodes[0].longitude, -73.0)
        self.assertIsNone(geocodes[0].created_at)
        self.assertIsNone(geocodes[0].updated_at)

    def test_property_to_csv_writes_declared_columns_and_values(self):
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            name="Warehouse",
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "properties.csv"
            Property.to_csv([property_object], path)
            with open(path, "r") as file:
                rows = list(csv.DictReader(file, dialect=csv.unix_dialect))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Warehouse")
        self.assertEqual(rows[0]["addressInput"], "1 Main Street")
        self.assertEqual(rows[0]["reitTicker"], "PLD")
        self.assertEqual(rows[0]["id"], "")


if __name__ == "__main__":
    unittest.main()
