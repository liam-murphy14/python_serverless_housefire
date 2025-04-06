import csv
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class SerializableHousefireObject(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data: dict) -> "SerializableHousefireObject":
        pass

    @staticmethod
    @abstractmethod
    def keys() -> list[str]:
        pass

    @staticmethod
    def to_csv(data: list["SerializableHousefireObject"], path: Path):
        with open(path, "w") as f:
            writer = csv.DictWriter(
                f, fieldnames=data[0].keys(), dialect=csv.unix_dialect
            )
            writer.writeheader()
            for d in data:
                data_dict = d.to_dict()
                writer.writerow(data_dict)

    @staticmethod
    @abstractmethod
    def from_csv(path: Path) -> list["SerializableHousefireObject"]:
        pass


@dataclass
class Geocode(SerializableHousefireObject):
    address_input: str
    latitude: float
    longitude: float
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    street_number: Optional[str] = None
    route: Optional[str] = None
    locality: Optional[str] = None
    administrative_area_level1: Optional[str] = None
    administrative_area_level2: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    formatted_address: Optional[str] = None
    global_plus_code: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Creates a dictionary representation of the Geocode object, omitting None values and the id, created_at, and
        updated_at fields
        """
        dict_with_none_values = {
            "addressInput": self.address_input,
            "streetNumber": self.street_number,
            "route": self.route,
            "locality": self.locality,
            "administrativeAreaLevel1": self.administrative_area_level1,
            "administrativeAreaLevel2": self.administrative_area_level2,
            "country": self.country,
            "postalCode": self.postal_code,
            "formattedAddress": self.formatted_address,
            "globalPlusCode": self.global_plus_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
        return {k: v for k, v in dict_with_none_values.items() if v is not None}

    @staticmethod
    def from_dict(data: dict) -> "Geocode":
        return Geocode(
            id=data["id"] if "id" in data else None,
            created_at=(
                datetime.fromisoformat(data["createdAt"])
                if "createdAt" in data
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updatedAt"])
                if "updatedAt" in data
                else None
            ),
            address_input=data["addressInput"],
            street_number=data["streetNumber"] if "streetNumber" in data else None,
            route=data["route"] if "route" in data else None,
            locality=data["locality"] if "locality" in data else None,
            administrative_area_level1=(
                data["administrativeAreaLevel1"]
                if "administrativeAreaLevel1" in data
                else None
            ),
            administrative_area_level2=(
                data["administrativeAreaLevel2"]
                if "administrativeAreaLevel2" in data
                else None
            ),
            country=data["country"] if "country" in data else None,
            postal_code=data["postalCode"] if "postalCode" in data else None,
            formatted_address=(
                data["formattedAddress"] if "formattedAddress" in data else None
            ),
            global_plus_code=(
                data["globalPlusCode"] if "globalPlusCode" in data else None
            ),
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
        )

    @staticmethod
    def keys() -> list[str]:
        return [
            "id",
            "createdAt",
            "updatedAt",
            "addressInput",
            "streetNumber",
            "route",
            "locality",
            "administrativeAreaLevel1",
            "administrativeAreaLevel2",
            "country",
            "postalCode",
            "formattedAddress",
            "globalPlusCode",
            "latitude",
            "longitude",
        ]

    @staticmethod
    def from_csv(path: Path) -> list["Geocode"]:
        with open(path, "r") as f:
            reader = csv.DictReader(f, dialect=csv.unix_dialect)
            data: list["Geocode"] = []
            for row in reader:
                data.append(Geocode.from_dict(row))
            return data


@dataclass
class Property(SerializableHousefireObject):
    address_input: str
    reit_ticker: str
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    square_footage: Optional[float] = None

    def to_dict(self) -> dict:
        """
        Creates a dictionary representation of the Property object, omitting None values and the id, created_at, and
        updated_at fields
        """
        dict_with_none_values = {
            "name": self.name,
            "addressInput": self.address_input,
            "address": self.address,
            "address2": self.address2,
            "neighborhood": self.neighborhood,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "squareFootage": self.square_footage,
            "reitTicker": self.reit_ticker,
        }
        return {k: v for k, v in dict_with_none_values.items() if v is not None}

    @staticmethod
    def from_dict(data: dict) -> "Property":
        return Property(
            id=data["id"] if "id" in data else None,
            created_at=(
                datetime.fromisoformat(data["createdAt"])
                if "createdAt" in data
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updatedAt"])
                if "updatedAt" in data
                else None
            ),
            name=data["name"] if "name" in data else None,
            address_input=data["addressInput"],
            address=data["address"] if "address" in data else None,
            address2=data["address2"] if "address2" in data else None,
            neighborhood=data["neighborhood"] if "neighborhood" in data else None,
            city=data["city"] if "city" in data else None,
            state=data["state"] if "state" in data else None,
            zip=data["zip"] if "zip" in data else None,
            country=data["country"] if "country" in data else None,
            latitude=float(data["latitude"]) if "latitude" in data else None,
            longitude=float(data["longitude"]) if "longitude" in data else None,
            square_footage=(
                float(data["squareFootage"]) if "squareFootage" in data else None
            ),
            reit_ticker=data["reitTicker"],
        )

    @staticmethod
    def keys() -> list[str]:
        return [
            "id",
            "createdAt",
            "updatedAt",
            "name",
            "addressInput",
            "address",
            "address2",
            "neighborhood",
            "city",
            "state",
            "zip",
            "country",
            "latitude",
            "longitude",
            "squareFootage",
            "reitTicker",
        ]

    @staticmethod
    def from_csv(path: Path) -> list["Property"]:
        with open(path, "r") as f:
            reader = csv.DictReader(f, dialect=csv.unix_dialect)
            data: list["Property"] = []
            for row in reader:
                data.append(Property.from_dict(row))
            return data
