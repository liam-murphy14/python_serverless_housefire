import requests as r
import uuid
import pandas as pd
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


# NOT CURRENTLY USED, BUT MAY BE USEFUL IN THE FUTURE
# TODO: instead of edge config nonsese, just add these objects to the REIT table in db
def format_edge_config_ciks():
    CIK_ENDPOINT = "https://sec.gov/files/company_tickers.json"
    to_concat_list = ["{"]
    reit_csv = pd.read_csv("adsf")  # TODO: change
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


# NOT CURRENTLY USED
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


# NOT CURRENTLY USED
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


TEMP_DIR_PATH = get_env_nonnull_path("TEMP_DIR_PATH")
CHROME_PATH = "@NIX_TARGET_CHROME_PATH@"  # set this at build time with nix
HOUSEFIRE_API_KEY = get_env_nonnull("HOUSEFIRE_API_KEY")
GOOGLE_MAPS_API_KEY = get_env_nonnull("GOOGLE_MAPS_API_KEY")
HOUSEFIRE_DEFAULT_BASE_URL = get_env_nonnull("HOUSEFIRE_DEFAULT_BASE_URL")
