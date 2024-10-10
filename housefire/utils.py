import requests as r
import uuid
import pandas as pd
from dotenv import load_dotenv
import os
from housefire.logger import get_logger

logger = get_logger(__name__)


def get_env_nonnull(key: str) -> str:
    """Get an environment variable and raise an error if it is None."""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable {key} is not set.")
    return value


def get_env_nonnull_path(key: str) -> str:
    """Get an environment variable and raise an error if it is None or does not exist."""
    value = get_env_nonnull(key)
    if not os.path.exists(value):
        raise ValueError(f"Path {value} does not exist.")
    return value


def get_env_nonnull_file(key: str) -> str:
    """Get an environment variable and raise an error if it is None or does not exist."""
    value = get_env_nonnull(key)
    if not os.path.isfile(value):
        raise ValueError(f"File {value} does not exist.")
    return value


def get_env_nonnull_dir(key: str) -> str:
    """Get an environment variable and raise an error if it is None or does not exist."""
    value = get_env_nonnull(key)
    if not os.path.isdir(value):
        raise ValueError(f"Directory {value} does not exist.")
    return value


# TODO: instead of edge config nonsese, just add these objects to the REIT table in db
def format_edge_config_ciks():
    CIK_ENDPOINT = "https://sec.gov/files/company_tickers.json"
    to_concat_list = ["{"]
    reit_csv = pd.read_csv(REIT_CSV_PATH)
    reit_set = set(reit_csv["Symbol"])
    cik_res = r.get(CIK_ENDPOINT)
    cik_data = cik_res.json()
    for key in cik_data:
        cik_str, ticker = str(cik_data[key]["cik_str"]), cik_data[key]["ticker"]
        if ticker not in reit_set:
            continue
        cik_str = cik_str.zfill(10)
        to_concat_list.append(f'     "{ticker}": "{cik_str}",')
    to_concat_list.append("}")
    return "\n".join(to_concat_list)


# TODO: start using this once nodriver is updated with experimental options
def create_temp_dir(base_path: str) -> str:
    """
    Create a new directory with a random name in the temp directory

    param: base_path: the path to the base directory to create the new directory in

    returns: the full path to the new directory
    """
    dir_name = str(uuid.uuid4())
    new_dir_path = os.path.join(base_path, dir_name)
    logger.debug(f"Creating temp directory at {new_dir_path}")
    os.mkdir(new_dir_path)
    logger.info(f"Created temp directory at {new_dir_path}")
    return new_dir_path


# TODO: start using this once nodriver is updated with experimental options
def delete_temp_dir(temp_dir_path: str) -> None:
    """
    Delete a directory and all of its contents
    USE WITH CAUTION

    param: temp_dir_path: the path to the directory to delete
    """
    logger.debug(f"Deleting directory at {temp_dir_path}")
    try:
        for filename in os.listdir(temp_dir_path):
            file_path = os.path.join(temp_dir_path, filename)
            logger.debug(f"Deleting file at {file_path}")
            os.remove(file_path)
        os.rmdir(temp_dir_path)
        logger.info(f"Deleted directory at {temp_dir_path}")
    except Exception as e:
        logger.error(f"Error deleting directory at {temp_dir_path}: {e}", exc_info=True)


def housefire_geocode_to_housefire_address(housefire_geocode: dict) -> dict:
    return {
        "addressInput": housefire_geocode["addressInput"],
        "address": f"{housefire_geocode['streetNumber']} {housefire_geocode['route']}",
        "neighborhood": housefire_geocode["locality"],
        "city": housefire_geocode["administrativeAreaLevel2"],
        "state": housefire_geocode["administrativeAreaLevel1"],
        "zip": housefire_geocode["postalCode"],
        "country": housefire_geocode["country"],
        "latitude": housefire_geocode["latitude"],
        "longitude": housefire_geocode["longitude"],
    }


def df_to_request(df: pd.DataFrame):
    """
    Convert a pandas DataFrame to a list of dictionaries
    """
    logger.debug(f"Converting DataFrame to request format for df: {df}")
    request_dict = df.to_dict(orient="records")
    logger.debug(f"Converted DataFrame to request format: {request_dict}")
    return request_dict


def acres_to_sqft(acres: float) -> float:
    return acres * 43560


def parse_area_unit(area: str) -> str:
    area_lower = area.lower()
    if "ac" in area_lower:
        return "acres"
    if "sf" in area_lower or "ft" in area_lower:
        return "sqft"
    raise ValueError(f"Unsupported area unit: {area}")


def parse_area_range(area: str) -> float:
    area_parts = area.split("-")
    if len(area_parts) > 2:
        raise ValueError(f"Unsupported area range: {area}")
    if len(area_parts) == 1:
        logger.debug(f"Found 1 area part: {area_parts[0]}")
        return parse_area_string(area_parts[0])
    logger.debug(f"Found 2 area parts: {area_parts[0]} and {area_parts[1]}, averaging")
    return (parse_area_string(area_parts[0]) + parse_area_string(area_parts[1])) / 2


def parse_and_convert_area(area: str) -> float:
    area_unit = parse_area_unit(area)
    area_value = parse_area_range(area)
    if area_unit == "acres":
        return acres_to_sqft(area_value)
    return area_value


def parse_area_string(area: str) -> float:
    digits = "".join(list(filter(str.isdigit, area)))
    return float(digits)


if __name__ == "__main__":
    load_dotenv()

    TEMP_DIR_PATH = os.getenv("TEMP_DIR")
    if TEMP_DIR_PATH is None:
        raise Exception("TEMP_DIR environment variable not set")
    REIT_CSV_PATH = os.path.join(TEMP_DIR_PATH, "reits.csv")
    if not os.path.exists(REIT_CSV_PATH):
        raise Exception(f"{REIT_CSV_PATH} does not exist")
    formatted_ciks = format_edge_config_ciks()
    print(formatted_ciks)
