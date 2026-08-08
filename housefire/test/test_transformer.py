import json
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

    def test_execute_transform_parses_ordered_property_facts(self):
        transformer = PldTransformer()
        transformer.ticker = "pld"
        result = ScrapeResult(
            {
                "Property Name": "Distribution Center",
                "Street Address 1": "1 Main Street",
                "City": "New York",
                "State": "NY",
                "Postal Code": "10001",
                "Country": "US",
                "Latitude": "40.0",
                "Longitude": "-73.0",
                "Available Date": "01/01/2027",
                "Market Property Type": "Building",
                "Truck Court Depth": "164.0000",
                "Rail Served": "No",
                "Key Feature 1": "30' Clear Height",
                "Key Feature 2": "89 Dock Doors",
                "Unit Name": "Hall A",
                "Unit Office Size": "17,555 SF",
                "# of Grade Level Doors": "12",
                "Warehouse Lighting Type": "LED",
                "Clear Height": "32 FT",
                "Main Breaker Size (AMPS)": "2,000",
                "Fire Suppression System": "ESFR",
                "# of Dock High Doors": "20",
            }
        )

        transformed = transformer.execute_transform([result])

        self.assertEqual(
            transformed[0].property.facts,
            [
                {"label": "Available Date", "value": "01/01/2027"},
                {"label": "Market Property Type", "value": "Building"},
                {"label": "Truck Court Depth", "value": "164.0000"},
                {"label": "Rail Served", "value": "No"},
                {"label": "Key Feature 1", "value": "30' Clear Height"},
                {"label": "Key Feature 2", "value": "89 Dock Doors"},
                {"label": "Unit Name", "value": "Hall A"},
                {"label": "Unit Office Size", "value": "17,555 SF"},
                {"label": "Grade Level Doors", "value": "12"},
                {"label": "Warehouse Lighting Type", "value": "LED"},
                {"label": "Clear Height", "value": "32 FT"},
                {"label": "Main Breaker Size (AMPS)", "value": "2,000"},
                {"label": "Fire Suppression System", "value": "ESFR"},
                {"label": "Dock High Doors", "value": "20"},
            ],
        )

    def test_execute_transform_omits_empty_and_placeholder_facts(self):
        transformer = PldTransformer()
        transformer.ticker = "pld"
        result = ScrapeResult(
            {
                "Latitude": "40.0",
                "Longitude": "-73.0",
                "Available Date": " ",
                "Truck Court Depth": " N/A ",
                "Rail Served": " No ",
                "Key Feature 1": "tBD",
                "Key Feature 2": "  Cross-dock loading  ",
                "Fire Suppression System": "",
            }
        )

        transformed = transformer.execute_transform([result])

        self.assertEqual(
            transformed[0].property.facts,
            [
                {"label": "Rail Served", "value": "No"},
                {"label": "Key Feature 2", "value": "Cross-dock loading"},
            ],
        )

    def test_execute_transform_uses_none_when_no_property_facts_apply(self):
        transformer = PldTransformer()
        transformer.ticker = "pld"
        result = ScrapeResult({"Latitude": "40.0", "Longitude": "-73.0"})

        transformed = transformer.execute_transform([result])

        self.assertIsNone(transformed[0].property.facts)


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

    def get_transformer_with_geocode(self):
        transformer = DlrTransformer()
        transformer.ticker = "dlr"
        transformer.logger = Mock()
        transformer.google_geocode_api_client = Mock()
        transformer.google_geocode_api_client.geocode_addresses.return_value = {
            "1 Main Street": Geocode("1 Main Street", 40.0, -73.0)
        }
        return transformer

    def test_execute_transform_sets_square_footage(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {"address_input": "1 Main Street", "square_footage": "12,500 SF"}
        )

        transformed = transformer.transform([result])

        self.assertEqual(transformed[0].property.square_footage, 12500.0)
        self.assertEqual(transformed[0].property.reit_ticker, "DLR")

    def test_execute_transform_maps_dlr_facts_in_source_order(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "name": "Chicago CH1",
                "address_input": "1 Main Street",
                "square_footage": "485,000 SF",
                "facility_code": "CH1",
                "description": "This center supports large deployments.",
                "facility_brochure_url": "https://go2.digitalrealty.com/ch1.pdf",
                "building_structure": "1 Story",
                "total_building_size": "485,000 ft² (45,050 m²)",
                "ups_redundancy": "N+2",
                "cooling_redundancy": "N+1",
                "compliance_certifications": json.dumps(["SOC1", "ISO 27001"]),
                "sustainability_certifications": json.dumps(["Energy Star"]),
                "sustainability_energy_label": "Carbon-Free Energy %",
                "sustainability_energy_value": "100%",
                "security_infrastructure": json.dumps(
                    ["24x7 onsite security personnel", "CCTV with 90 day backup"]
                ),
            }
        )

        transformed = transformer.transform([result])

        self.assertEqual(transformed[0].property.name, "Chicago CH1")
        self.assertEqual(transformed[0].property.square_footage, 485000.0)
        self.assertEqual(
            transformed[0].property.facts,
            [
                {"label": "Facility Code", "value": "CH1"},
                {
                    "label": "Description",
                    "value": "This center supports large deployments.",
                },
                {
                    "label": "Facility Brochure",
                    "value": "https://go2.digitalrealty.com/ch1.pdf",
                },
                {"label": "Building Structure", "value": "1 Story"},
                {
                    "label": "Total Building Size",
                    "value": "485,000 ft² (45,050 m²)",
                },
                {"label": "UPS Redundancy", "value": "N+2"},
                {"label": "Cooling Redundancy", "value": "N+1"},
                {"label": "Compliance Certification", "value": "SOC1"},
                {"label": "Compliance Certification", "value": "ISO 27001"},
                {"label": "Sustainability Certification", "value": "Energy Star"},
                {"label": "Carbon-Free Energy %", "value": "100%"},
                {
                    "label": "Security & Infrastructure",
                    "value": "24x7 onsite security personnel",
                },
                {
                    "label": "Security & Infrastructure",
                    "value": "CCTV with 90 day backup",
                },
            ],
        )

    def test_execute_transform_omits_missing_optional_dlr_facts(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "name": "CH1",
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
            }
        )

        transformed = transformer.transform([result])

        self.assertIsNone(transformed[0].property.facts)

    def test_execute_transform_handles_blank_optional_facts_after_csv_round_trip(self):
        transformer = self.get_transformer_with_geocode()
        transformer.google_geocode_api_client.geocode_addresses.return_value = {
            "1 Main Street": Geocode("1 Main Street", 40.0, -73.0),
            "2 Main Street": Geocode("2 Main Street", 41.0, -74.0),
        }
        complete = ScrapeResult(
            {
                "name": "CH1",
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
                "facility_code": "CH1",
                "compliance_certifications": json.dumps(["SOC 2"]),
                "sustainability_certifications": json.dumps(["Energy Star"]),
                "sustainability_energy_label": "Renewable Energy %",
                "sustainability_energy_value": "14%",
                "security_infrastructure": json.dumps(["CCTV"]),
            }
        )
        missing_optional_facts = ScrapeResult(
            {"name": "CH2", "address_input": "2 Main Street"}
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dlr-scrape.csv"
            ScrapeResult.to_csv([complete, missing_optional_facts], path)
            round_tripped = ScrapeResult.from_csv(path)

        self.assertEqual(
            round_tripped[1].property_info["compliance_certifications"], ""
        )
        self.assertEqual(
            round_tripped[1].property_info["sustainability_energy_value"], ""
        )
        self.assertEqual(round_tripped[1].property_info["security_infrastructure"], "")

        transformed = transformer.transform(round_tripped)

        self.assertEqual(
            transformed[0].property.facts,
            [
                {"label": "Facility Code", "value": "CH1"},
                {"label": "Compliance Certification", "value": "SOC 2"},
                {"label": "Sustainability Certification", "value": "Energy Star"},
                {"label": "Renewable Energy %", "value": "14%"},
                {"label": "Security & Infrastructure", "value": "CCTV"},
            ],
        )
        self.assertIsNone(transformed[1].property.facts)
        self.assertIsNone(transformed[1].property.square_footage)

    def test_execute_transform_uses_none_for_missing_square_footage(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult({"address_input": "1 Main Street"})

        transformed = transformer.transform([result])

        self.assertIsNone(transformed[0].property.square_footage)

    def test_execute_transform_rejects_malformed_present_square_footage(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {"address_input": "1 Main Street", "square_footage": "not listed"}
        )

        with self.assertRaises(ValueError):
            transformer.transform([result])

    def test_execute_transform_omits_blank_and_placeholder_dlr_facts(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
                "facility_code": " N/A ",
                "description": "  Available in Q4  ",
                "building_structure": " tBd ",
                "compliance_certifications": json.dumps(
                    [" SOC 2 ", "n/a", " ", "ISO 27001", "TBD"]
                ),
                "sustainability_certifications": json.dumps(["  Energy Star  ", "N/A"]),
                "sustainability_energy_label": " tBd ",
                "sustainability_energy_value": " N/A ",
                "security_infrastructure": json.dumps(
                    [" N/A ", " CCTV ", "", "tbd", "Onsite guards"]
                ),
            }
        )

        transformed = transformer.transform([result])

        self.assertEqual(
            transformed[0].property.facts,
            [
                {"label": "Description", "value": "Available in Q4"},
                {"label": "Compliance Certification", "value": "SOC 2"},
                {"label": "Compliance Certification", "value": "ISO 27001"},
                {"label": "Sustainability Certification", "value": "Energy Star"},
                {"label": "Security & Infrastructure", "value": "CCTV"},
                {"label": "Security & Infrastructure", "value": "Onsite guards"},
            ],
        )

    def test_execute_transform_rejects_incomplete_meaningful_energy_fact(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
                "sustainability_energy_label": "Renewable Energy %",
                "sustainability_energy_value": "TBD",
            }
        )

        with self.assertRaises(ValueError):
            transformer.transform([result])

    def test_execute_transform_preserves_dynamic_sustainability_label(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "name": "CH1",
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
                "sustainability_energy_label": "Renewable Energy %",
                "sustainability_energy_value": "14%",
            }
        )

        transformed = transformer.transform([result])

        self.assertIn(
            {"label": "Renewable Energy %", "value": "14%"},
            transformed[0].property.facts,
        )

    def test_execute_transform_rejects_malformed_dlr_fact_json(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "name": "CH1",
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
                "security_infrastructure": "not-json",
            }
        )

        with self.assertRaises(ValueError):
            transformer.transform([result])


if __name__ == "__main__":
    unittest.main()
