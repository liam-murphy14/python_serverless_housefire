from housefire.transformer.transformer import Transformer, TransformResult
from housefire.dependency.housefire_client.housefire_object import Property
from housefire.scraper.scraper import ScrapeResult


class PldTransformer(Transformer):
    facts_field_map = (
        ("Available Date", "Available Date"),
        ("Market Property Type", "Market Property Type"),
        ("Truck Court Depth", "Truck Court Depth"),
        ("Rail Served", "Rail Served"),
        *((f"Key Feature {index}", f"Key Feature {index}") for index in range(1, 7)),
        ("Unit Name", "Unit Name"),
        ("Unit Office Size", "Unit Office Size"),
        ("# of Grade Level Doors", "Grade Level Doors"),
        ("Warehouse Lighting Type", "Warehouse Lighting Type"),
        ("Clear Height", "Clear Height"),
        ("Main Breaker Size (AMPS)", "Main Breaker Size (AMPS)"),
        ("Fire Suppression System", "Fire Suppression System"),
        ("# of Dock High Doors", "Dock High Doors"),
    )

    def __init__(self):
        super().__init__()

        self.column_names_map = {
            "Property Name": "name",
            "Street Address 1": "address",
            "Street Address 2": "address2",
            "Neighborhood": "neighborhood",
            "City": "city",
            "State": "state",
            "Postal Code": "zip",
            "Country": "country",
            "Latitude": "latitude",
            "Longitude": "longitude",
            "Available Square Footage": "squareFootage",
        }

    def execute_transform(self, data: list[ScrapeResult]) -> list[TransformResult]:
        results: list[TransformResult] = list()
        for result in data:
            prop_info = result.property_info
            prop = Property(
                name=(
                    prop_info["Property Name"] if "Property Name" in prop_info else None
                ),
                address=(
                    prop_info["Street Address 1"]
                    if "Street Address 1" in prop_info
                    else None
                ),
                address2=(
                    prop_info["Street Address 2"]
                    if "Street Address 2" in prop_info
                    else None
                ),
                neighborhood=(
                    prop_info["Neighborhood"] if "Neighborhood" in prop_info else None
                ),
                city=prop_info["City"] if "City" in prop_info else None,
                state=prop_info["State"] if "State" in prop_info else None,
                zip=prop_info["Postal Code"] if "Postal Code" in prop_info else None,
                country=prop_info["Country"] if "Country" in prop_info else None,
                latitude=float(prop_info["Latitude"]),
                longitude=float(prop_info["Longitude"]),
                square_footage=(
                    self.parse_and_convert_area(prop_info["Available Square Footage"])
                    if "Available Square Footage" in prop_info
                    else None
                ),
                facts=self._parse_facts(prop_info),
                address_input=self._construct_address_input(prop_info),
                reit_ticker=self.ticker,
            )
            results.append(TransformResult(property=prop, scrape_result=result))
        return results

    @classmethod
    def _parse_facts(cls, prop_info: dict) -> list[dict[str, str]] | None:
        facts = []
        for source_field, label in cls.facts_field_map:
            value = prop_info.get(source_field)
            if value is None:
                continue
            value = value.strip()
            if not value or value.upper() in {"N/A", "TBD"}:
                continue
            facts.append({"label": label, "value": value})
        return facts or None

    @staticmethod
    def _construct_address_input(prop_info: dict) -> str:
        address = prop_info.get("Street Address 1", "")
        city = prop_info.get("City", "")
        state = prop_info.get("State", "")
        zip_code = prop_info.get("Postal Code", "")
        country = prop_info.get("Country", "")

        return f"{address}, {city}, {state} {zip_code}, {country}" if address else ""
