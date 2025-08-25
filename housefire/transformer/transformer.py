from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from housefire.dependency.housefire_client.housefire_object import Property
from housefire.scraper.scraper import ScrapeResult


class Transformer(ABC):

    # injected by factory
    logger: Logger
    ticker: str

    def __init__(self):
        pass

    @abstractmethod
    def execute_transform(self, data: list[ScrapeResult]) -> list["TransformResult"]:
        return NotImplemented

    def _debug_transform(self, data: list[ScrapeResult]) -> list["TransformResult"]:
        """
        debugging method to transform data at a small scale, can be used for manual testing
        """
        head: list[ScrapeResult] = data[:5] if len(data) > 5 else data
        return self.transform(head)

    def transform(self, data: list[ScrapeResult]) -> list["TransformResult"]:
        """
        transform data and log
        """
        self.logger.debug(f"Transforming data for REIT: {self.ticker}, df: {data}")
        transformed_data = self.execute_transform(data)
        duplicate_addresses = set()
        results = list()

        # drop duplicates and upper case reit tickers
        for result in transformed_data:
            result.property.reit_ticker = self.ticker.upper()
            if result.property.address_input in duplicate_addresses:
                self.logger.debug(f"Dropping duplicate: {result}")
                continue
            duplicate_addresses.add(result.property.address_input)
            results.append(result)

        self.logger.debug(
            f"Transformed data for REIT: {self.ticker}, results: {results}"
        )
        return results

    @staticmethod
    def acres_to_sqft(acres: float) -> float:
        return acres * 43560

    @staticmethod
    def parse_area_unit(area: str) -> str:
        area_lower = area.lower()
        if "ac" in area_lower:
            return "acres"
        if "sf" in area_lower or "ft" in area_lower:
            return "sqft"
        raise ValueError(f"Unsupported area unit: {area}")

    @classmethod
    def parse_area_range(cls, area: str) -> float:
        area_parts = area.split("-")
        if len(area_parts) > 2:
            raise ValueError(f"Unsupported area range: {area}")
        if len(area_parts) == 1:
            return cls.parse_area_string(area_parts[0])
        return (
            cls.parse_area_string(area_parts[0]) + cls.parse_area_string(area_parts[1])
        ) / 2

    @classmethod
    def parse_and_convert_area(cls, area: str) -> float:
        area_unit = cls.parse_area_unit(area)
        area_value = cls.parse_area_range(area)
        if area_unit == "acres":
            return cls.acres_to_sqft(area_value)
        return area_value

    @staticmethod
    def parse_area_string(area: str) -> float:
        digits = "".join(list(filter(str.isdigit, area)))
        return float(digits)


@dataclass
class TransformResult:
    property: Property
    # TODO: remove scraperesult ???
    scrape_result: ScrapeResult

    @staticmethod
    def to_csv(data: list["TransformResult"], destination_path: Path) -> None:
        Property.to_csv([d.property for d in data], destination_path)

    @staticmethod
    def from_csv(file_path: Path) -> list["TransformResult"]:
        return [
            TransformResult(property=p, scrape_result=ScrapeResult(dict()))
            for p in Property.from_csv(file_path)
        ]
