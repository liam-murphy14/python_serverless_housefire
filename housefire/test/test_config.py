import configparser
import unittest

from housefire.config import HousefireConfig


class TestHousefireConfig(unittest.TestCase):

    TEST_HOUSEFIRE_CONFIG_KEY = "HOUSEFIRE"

    TEST_TEMP_DIR_PATH = "/tmp"
    TEST_HOUSEFIRE_API_KEY = "123"
    TEST_GOOGLE_MAPS_API_KEY = "456"
    TEST_HOUSEFIRE_BASE_URL = "https://example.com"
    TEST_DEPLOY_ENV = "dev"

    TEST_UNREPLACED_CHROME_PATH = "@NIX_TARGET_CHROME_PATH@"

    def test_constructor_with_initialized_config_has_attributes(self):
        config_object = self.get_initialized_config()
        housefire_config = HousefireConfig(config_object)
        self.assertEqual(housefire_config.temp_dir_path, self.TEST_TEMP_DIR_PATH)
        self.assertEqual(
            housefire_config.housefire_api_key, self.TEST_HOUSEFIRE_API_KEY
        )
        self.assertEqual(
            housefire_config.google_maps_api_key, self.TEST_GOOGLE_MAPS_API_KEY
        )
        self.assertEqual(
            housefire_config.housefire_base_url, self.TEST_HOUSEFIRE_BASE_URL
        )
        self.assertEqual(housefire_config.deploy_env, self.TEST_DEPLOY_ENV)

    def test_constructor_with_missing_section_raises_value_error(self):
        config_object = self.get_config_with_missing_section()
        with self.assertRaises(ValueError):
            HousefireConfig(config_object)

    def test_constructor_with_missing_temp_dir_path_raises_value_error(self):
        config_object = self.get_config_with_missing_temp_dir_path()
        with self.assertRaises(ValueError):
            HousefireConfig(config_object)

    def get_initialized_config(self):
        config_object = configparser.ConfigParser()
        config_object[self.TEST_HOUSEFIRE_CONFIG_KEY] = {
            "TEMP_DIR_PATH": self.TEST_TEMP_DIR_PATH,
            "HOUSEFIRE_API_KEY": self.TEST_HOUSEFIRE_API_KEY,
            "GOOGLE_MAPS_API_KEY": self.TEST_GOOGLE_MAPS_API_KEY,
            "HOUSEFIRE_BASE_URL": self.TEST_HOUSEFIRE_BASE_URL,
            "DEPLOY_ENV": self.TEST_DEPLOY_ENV,
        }
        return config_object

    def get_config_with_missing_section(self):
        config_object = configparser.ConfigParser()
        return config_object

    def get_config_with_missing_temp_dir_path(self):
        config_object = self.get_initialized_config()
        del config_object[self.TEST_HOUSEFIRE_CONFIG_KEY]["TEMP_DIR_PATH"]
        return config_object


if __name__ == "__main__":
    unittest.main()
