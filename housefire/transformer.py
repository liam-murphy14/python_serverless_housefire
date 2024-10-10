import pandas as pd
import numpy as np
from housefire.dependency import HousefireAPI, GoogleGeocodeAPI
from housefire.logger import get_logger
from housefire.utils import (
    get_env_nonnull,
    df_to_request,
    parse_and_convert_area,
    parse_area_string,
    housefire_geocode_to_housefire_address,
)
import dotenv

dotenv.load_dotenv()

housefire_api_client = HousefireAPI(get_env_nonnull("HOUSEFIRE_API_KEY"))
google_geocode_api_client = GoogleGeocodeAPI(
    get_env_nonnull("GOOGLE_MAPS_API_KEY"), housefire_api_client
)

logger = get_logger(__name__)


def _geocode_transform(df: pd.DataFrame) -> pd.DataFrame:
    address_inputs = df["address"].to_list()
    df.drop(columns=["address"], inplace=True)
    records = df.to_dict(orient="records")
    housefire_geocodes = google_geocode_api_client.geocode_addresses(address_inputs)
    for address_input, record in zip(address_inputs, records):
        record["addressInput"] = address_input
        if address_input not in housefire_geocodes:
            logger.error(f"Failed to geocode address: {address_input}")
            continue
        housefire_geocode = housefire_geocodes[address_input]
        record.update(housefire_geocode_to_housefire_address(housefire_geocode))
    return pd.DataFrame(records)


PLD_UNNECESSARY_COLUMNS = [
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

PLD_COLUMN_NAMES_MAP = {
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


def _pld_transform(df: pd.DataFrame) -> pd.DataFrame:
    df.drop(
        columns=PLD_UNNECESSARY_COLUMNS,
        inplace=True,
        axis=1,
    )
    df.rename(
        PLD_COLUMN_NAMES_MAP,
        inplace=True,
        axis=1,
    )
    df = df.astype({"zip": "str"})
    df["squareFootage"] = df["squareFootage"].apply(parse_and_convert_area)
    df["addressInput"] = df.agg(
        lambda x: f"{x['address']}, {x['city']}, {x['state']} {x['zip']}, {x['country']}",
        axis=1,
    )
    return df


def _eqix_transform(df: pd.DataFrame) -> pd.DataFrame:
    return _geocode_transform(df)


def _welltower_transform(df: pd.DataFrame) -> pd.DataFrame:
    return _geocode_transform(df)


def _simon_transform(df: pd.DataFrame) -> pd.DataFrame:
    return _geocode_transform(df)


def _digital_realty_transform(df: pd.DataFrame) -> pd.DataFrame:
    df["squareFootage"] = df["squareFootage"].apply(parse_area_string)
    return _geocode_transform(df)


TRANSFORMERS = {
    "pld": _pld_transform,
    "eqix": _eqix_transform,
    "well": _welltower_transform,
    "spg": _simon_transform,
    "dlr": _digital_realty_transform,
}


def transform_wrapper(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Transform data and log
    """
    custom_transform = TRANSFORMERS[ticker]
    logger.debug(f"Transforming data for REIT: {ticker}, df: {data}")
    transformed_data = custom_transform(data)
    transformed_data.fillna(np.nan, inplace=True)
    transformed_data.replace([np.nan], [None], inplace=True)
    transformed_data_with_ticker = transformed_data.assign(reitTicker=ticker.upper())
    duplicates = transformed_data_with_ticker.duplicated(subset="addressInput")
    logger.debug(f"Dropping duplicates: {duplicates}")
    transformed_data_with_ticker.drop_duplicates(inplace=True, subset="addressInput")
    logger.debug(
        f"Transformed data for REIT: {ticker}, df: {transformed_data_with_ticker}"
    )
    return transformed_data_with_ticker


if __name__ == "__main__":

    # HOUSEFIRE TEST
    dotenv.load_dotenv()
    
    HOUSEFIRE_API_KEY = get_env_nonnull("HOUSEFIRE_API_KEY")

    # api = HousefireAPI(HOUSEFIRE_API_KEY)
    # api.base_url = "http://localhost:5173/api/"
    # pld_test_df = pd.read_csv("/Users/liammurphy/Downloads/Data_export.csv")
    # transformed = transform_wrapper(pld_test_df, "pld")
    # request = df_to_request(transformed)
    # response = api.post_properties(request)
    # logger.info(f"resjsno: {response.json()}")

    # GOOGLE MAPS TEST

    # realty_df = pd.DataFrame(
    #     {
    #         "name": ["Chicago CH2"],
    #         "address": ["2200 Busse Road, Elk Grove Village, IL 60007"],
    #         "squareFootage": ["485,000"],
    #     }
    # )
    # print(_digital_realty_transform(realty_df))
    properties_dataframe = pd.read_csv("/Users/liammurphy/Downloads/Data_export.csv")
    ticker = "pld"
    transformed_dataframe = transform_wrapper(properties_dataframe, ticker)
    logger.debug(f"Transformed properties data: {transformed_dataframe}")

    housefire_api = HousefireAPI(HOUSEFIRE_API_KEY, base_url="http://localhost:5173/api/")

    created_properties = housefire_api.update_properties_by_ticker(
        ticker.upper(), df_to_request(transformed_dataframe)
    )
    logger.info(f"Created properties: {created_properties}")
