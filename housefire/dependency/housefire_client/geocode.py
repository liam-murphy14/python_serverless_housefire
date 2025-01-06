from dataclasses import dataclass
from datetime import datetime

@dataclass
class Geocode:
    id: str | None
    created_at: datetime | None
    updated_at: datetime | None
    address_input: str
    street_number: str | None
    route: str | None
    locality: str | None
    administrative_area_level1: str | None
    administrative_area_level2: str | None
    country: str | None
    postal_code: str | None
    formatted_address: str | None
    global_plus_code: str | None
    latitude: float
    longitude: float

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
    def from_dict(data: dict) -> 'Geocode':
        return Geocode(
                id=data["id"] if "id" in data else None,
                created_at=data["createdAt"] if "createdAt" in data else None,
                updated_at=data["updatedAt"] if "updatedAt" in data else None,
                address_input=data["addressInput"],
                street_number=data["streetNumber"] if "streetNumber" in data else None,
                route=data["route"] if "route" in data else None,
                locality=data["locality"] if "locality" in data else None,
                administrative_area_level1=data["administrativeAreaLevel1"] if "administrativeAreaLevel1" in data else None,
                administrative_area_level2=data["administrativeAreaLevel2"] if "administrativeAreaLevel2" in data else None,
                country=data["country"] if "country" in data else None,
                postal_code=data["postalCode"] if "postalCode" in data else None,
                formatted_address=data["formattedAddress"] if "formattedAddress" in data else None,
                global_plus_code=data["globalPlusCode"] if "globalPlusCode" in data else None,
                latitude=data["latitude"],
                longitude=data["longitude"],
                )
