import pandas as pd
from housefire.dependency.google_maps import GoogleGeocodeAPI
from housefire.dependency.housefire_api import HousefireAPI
from housefire.transformer.transformer import Transformer


class GeocodeTransformer(Transformer):
    """
    Transformer that geocodes addresses during the transformation process.
    """

    # instantiated by factory
    google_geocode_api_client: GoogleGeocodeAPI


    def __init__(self):
        super().__init__()


    def _geocode_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        geocodes addresses in dataframe by calling housefire api to get geocode for each df["address"] entry,
        calling google geocode api if housefire api does not have the geocode and saving the result in housefire,
        then populating the dataframe fields with the geocode data
        """
        address_inputs = df["address"].to_list()
        df.drop(columns=["address"], inplace=True)
        records = df.to_dict(orient="records")
        housefire_geocodes = self.google_geocode_api_client.geocode_addresses(
            address_inputs
        )
        for address_input, record in zip(address_inputs, records):
            record["addressInput"] = address_input
            if address_input not in housefire_geocodes:
                self.logger.error(f"Failed to geocode address: {address_input}")
                continue
            housefire_geocode = housefire_geocodes[address_input]
            record.update(
                HousefireAPI.housefire_geocode_to_housefire_address(housefire_geocode)
            )
        return pd.DataFrame(records)
