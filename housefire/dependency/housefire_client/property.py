from dataclasses import dataclass
from datetime import datetime

@dataclass
class Property:
    id: str | None
    created_at: datetime | None
    updated_at: datetime | None
    name: str | None
    address_input: str
    address: str | None
    address2: str | None
    neighborhood: str | None
    city: str | None
    state: str | None
    zip: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    square_footage: float | None
    reit_ticker: str

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
    def from_dict(data: dict) -> 'Property':
        return Property(
            id=data["id"] if "id" in data else None,
            created_at=data["createdAt"] if "createdAt" in data else None,
            updated_at=data["updatedAt"] if "updatedAt" in data else None,
            name=data["name"] if "name" in data else None,
            address_input=data["addressInput"],
            address=data["address"] if "address" in data else None,
            address2=data["address2"] if "address2" in data else None,
            neighborhood=data["neighborhood"] if "neighborhood" in data else None,
            city=data["city"] if "city" in data else None,
            state=data["state"] if "state" in data else None,
            zip=data["zip"] if "zip" in data else None,
            country=data["country"] if "country" in data else None,
            latitude=data["latitude"] if "latitude" in data else None,
            longitude=data["longitude"] if "longitude" in data else None,
            square_footage=data["squareFootage"] if "squareFootage" in data else None,
            reit_ticker=data["reitTicker"],
        )
