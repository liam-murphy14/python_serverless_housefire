import json

from housefire.transformer.transformer import TransformResult
from housefire.scraper.scraper import ScrapeResult
from housefire.transformer.geocode_transformer import GeocodeTransformer


class DlrTransformer(GeocodeTransformer):
    facts_field_map = (
        ("facility_code", "Facility Code"),
        ("description", "Description"),
        ("facility_brochure_url", "Facility Brochure"),
        ("building_structure", "Building Structure"),
        ("total_building_size", "Total Building Size"),
        ("ups_redundancy", "UPS Redundancy"),
        ("cooling_redundancy", "Cooling Redundancy"),
    )

    def __init__(self):
        super().__init__()

    def execute_transform(self, data: list[ScrapeResult]) -> list[TransformResult]:
        results_with_geocode = self._geocode_transform(data)
        for result in results_with_geocode:
            result.property.name = result.scrape_result.property_info.get("name")
            result.property.facts = self._parse_facts(
                result.scrape_result.property_info
            )
            result.property.square_footage = self.parse_area_string(
                result.scrape_result.property_info["square_footage"]
            )
        return results_with_geocode

    @classmethod
    def _parse_facts(cls, prop_info):
        facts = []
        for source_field, label in cls.facts_field_map:
            value = prop_info.get(source_field)
            normalized = value.strip() if value is not None else ""
            if normalized and normalized.upper() not in {"N/A", "TBD"}:
                facts.append({"label": label, "value": normalized})

        list_fields = (
            ("compliance_certifications", "Compliance Certification"),
            ("sustainability_certifications", "Sustainability Certification"),
        )
        for source_field, label in list_fields:
            encoded_values = prop_info.get(source_field)
            if encoded_values is None:
                continue
            values = json.loads(encoded_values)
            if not isinstance(values, list):
                raise ValueError(f"Expected a list for {source_field}")
            for value in values:
                if not isinstance(value, str):
                    raise ValueError(f"Expected string values for {source_field}")
                if value.strip():
                    facts.append({"label": label, "value": value.strip()})

        energy_label = prop_info.get("sustainability_energy_label")
        energy_value = prop_info.get("sustainability_energy_value")
        if energy_label is not None or energy_value is not None:
            if not energy_label or not energy_value:
                raise ValueError("Incomplete sustainability energy fact")
            facts.append({"label": energy_label.strip(), "value": energy_value.strip()})

        encoded_security_values = prop_info.get("security_infrastructure")
        if encoded_security_values is not None:
            security_values = json.loads(encoded_security_values)
            if not isinstance(security_values, list):
                raise ValueError("Expected a list for security_infrastructure")
            for value in security_values:
                if not isinstance(value, str):
                    raise ValueError(
                        "Expected string values for security_infrastructure"
                    )
                if value.strip():
                    facts.append(
                        {"label": "Security & Infrastructure", "value": value.strip()}
                    )
        return facts or None
