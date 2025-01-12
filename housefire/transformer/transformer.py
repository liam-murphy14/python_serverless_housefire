from abc import ABC, abstractmethod
from logging import Logger
import pandas as pd
import numpy as np


class Transformer(ABC):

    # injected by factory
    logger: Logger
    ticker: str

    def __init__(self):
        pass

    @abstractmethod
    def execute_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        return NotImplemented

    def _debug_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        debugging method to transform data at a small scale, can be used for manual testing
        """
        head = data.head().copy()
        return self.transform(head)

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        transform data and log
        """
        self.logger.debug(f"Transforming data for REIT: {self.ticker}, df: {data}")
        transformed_data = self.execute_transform(data)
        transformed_data.fillna(np.nan, inplace=True)
        transformed_data.replace([np.nan], [None], inplace=True)
        transformed_data_with_ticker = transformed_data.assign(
            reitTicker=self.ticker.upper()
        )
        duplicates = transformed_data_with_ticker.duplicated(subset="addressInput")
        self.logger.debug(f"Dropping duplicates: {duplicates}")
        transformed_data_with_ticker.drop_duplicates(
            inplace=True, subset="addressInput"
        )
        self.logger.debug(
            f"Transformed data for REIT: {self.ticker}, df: {transformed_data_with_ticker}"
        )
        return transformed_data_with_ticker

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
