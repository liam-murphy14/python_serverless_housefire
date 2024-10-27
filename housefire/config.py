from dataclasses import dataclass
import configparser


@dataclass()
class HousefireConfig:
    """Class for accessing housefire configuration"""

    temp_dir_path: str
    housefire_api_key: str
    google_maps_api_key: str
    housefire_base_url: str
    deploy_env: str
    # set this at build time with nix
    chrome_path: str = "@NIX_TARGET_CHROME_PATH@"

    def __init__(self, config_object: configparser.ConfigParser):
        if not self.is_initialized(config_object):
            raise ValueError("Config object is not initialized")
        self.temp_dir_path = config_object["HOUSEFIRE"].get("TEMP_DIR_PATH")
        self.housefire_api_key = config_object["HOUSEFIRE"].get("HOUSEFIRE_API_KEY")
        self.google_maps_api_key = config_object["HOUSEFIRE"].get("GOOGLE_MAPS_API_KEY")
        self.housefire_base_url = config_object["HOUSEFIRE"].get("HOUSEFIRE_BASE_URL")
        self.deploy_env = config_object["HOUSEFIRE"].get("DEPLOY_ENV")

    def is_initialized(self, config_object: configparser.ConfigParser):
        return (
            "HOUSEFIRE" in config_object
            and "TEMP_DIR_PATH" in config_object["HOUSEFIRE"]
            and "HOUSEFIRE_API_KEY" in config_object["HOUSEFIRE"]
            and "GOOGLE_MAPS_API_KEY" in config_object["HOUSEFIRE"]
            and "HOUSEFIRE_BASE_URL" in config_object["HOUSEFIRE"]
        )
