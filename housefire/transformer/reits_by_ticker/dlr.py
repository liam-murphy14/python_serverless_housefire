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
            square_footage = result.scrape_result.property_info.get("square_footage")
            result.property.square_footage = (
                self.parse_area_string(square_footage)
                if square_footage is not None and square_footage.strip()
                else None
            )
        return results_with_geocode

    @staticmethod
    def _normalize_fact_value(value):
        if value is None:
            return None
        normalized = value.strip()
        if not normalized or normalized.upper() in {"N/A", "TBD"}:
            return None
        return normalized

    @classmethod
    def _parse_facts(cls, prop_info):
        facts = []
        for source_field, label in cls.facts_field_map:
            normalized = cls._normalize_fact_value(prop_info.get(source_field))
            if normalized:
                facts.append({"label": label, "value": normalized})

        list_fields = (
            ("compliance_certifications", "Compliance Certification"),
            ("sustainability_certifications", "Sustainability Certification"),
        )
        for source_field, label in list_fields:
            encoded_values = cls._normalize_fact_value(prop_info.get(source_field))
            if not encoded_values:
                continue
            values = json.loads(encoded_values)
            if not isinstance(values, list):
                raise ValueError(f"Expected a list for {source_field}")
            for value in values:
                if not isinstance(value, str):
                    raise ValueError(f"Expected string values for {source_field}")
                normalized = cls._normalize_fact_value(value)
                if normalized:
                    facts.append({"label": label, "value": normalized})

        energy_label = cls._normalize_fact_value(
            prop_info.get("sustainability_energy_label")
        )
        energy_value = cls._normalize_fact_value(
            prop_info.get("sustainability_energy_value")
        )
        if energy_label or energy_value:
            if not energy_label or not energy_value:
                raise ValueError("Incomplete sustainability energy fact")
            facts.append({"label": energy_label, "value": energy_value})

        encoded_security_values = cls._normalize_fact_value(
            prop_info.get("security_infrastructure")
        )
        if encoded_security_values:
            security_values = json.loads(encoded_security_values)
            if not isinstance(security_values, list):
                raise ValueError("Expected a list for security_infrastructure")
            for value in security_values:
                if not isinstance(value, str):
                    raise ValueError(
                        "Expected string values for security_infrastructure"
                    )
                normalized = cls._normalize_fact_value(value)
                if normalized:
                    facts.append(
                        {"label": "Security & Infrastructure", "value": normalized}
                    )
        return facts or None
