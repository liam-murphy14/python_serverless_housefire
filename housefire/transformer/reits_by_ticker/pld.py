import pandas as pd
from housefire.transformer.transformer import Transformer


class PldTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.ticker = "pld"
        self.unnecessary_columns = [
            "Available Date",
            "Market Property Type",
            "Link To Property Search Page",
            "Digital Tour URL",
            "Video URL",
            "Microsite URL",
            "Property Marketing Collateral URL",
            "Truck Court Depth",
            "Rail Served",
            "Broker Name",
            "Broker Email Address",
            "Broker Telephone Number",
            "Leasing Agent Name",
            "Leasing Agent Email Address",
            "Leasing Agent Telephone Number",
            "Unit Name",
            "Unit Office Size",
            "# of Grade Level Doors",
            "Warehouse Lighting Type",
            "Clear Height",
            "Main Breaker Size (AMPS)",
            "Fire Suppression System",
            "# of Dock High Doors",
            "Key Feature 1",
            "Key Feature 2",
            "Key Feature 3",
            "Key Feature 4",
            "Key Feature 5",
            "Key Feature 6",
        ]

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

    def execute_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        data.drop(
            columns=self.unnecessary_columns,
            inplace=True,
            axis=1,
        )
        data.rename(
            self.column_names_map,
            inplace=True,
            axis=1,
        )
        data = data.astype({"zip": "str"})
        data["squareFootage"] = data["squareFootage"].apply(self.parse_and_convert_area)
        data["addressInput"] = data.agg(
            lambda x: f"{x['address']}, {x['city']}, {x['state']} {x['zip']}, {x['country']}",
            axis=1,
        )
        return data
