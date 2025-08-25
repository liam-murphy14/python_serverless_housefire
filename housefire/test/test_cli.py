import unittest
from unittest.mock import patch, MagicMock, call, mock_open
from click.testing import CliRunner
import os
import configparser

from housefire import cli
from housefire.config import HousefireConfig
from housefire.scraper.scraper import ScrapeResult
from housefire.transformer.transformer import TransformResult


class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.configparser.ConfigParser")
    def test_housefire_group_no_config_file(self, mock_config_parser, mock_exists):
        mock_exists.return_value = False
        result = self.runner.invoke(cli.housefire, ["scrape", "DLR"])
        self.assertIn(
            "Looks like there is no config file",
            result.output,
        )
        self.assertEqual(result.exit_code, 0)

    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.configparser.ConfigParser")
    @patch("housefire.cli.HousefireConfig")
    def test_housefire_group_invalid_config_file(
        self, mock_housefire_config, mock_config_parser, mock_exists
    ):
        mock_exists.return_value = True
        mock_housefire_config.side_effect = ValueError("Invalid config")
        result = self.runner.invoke(cli.housefire, ["scrape", "DLR"])
        self.assertIn(
            "Looks like your config file at",
            result.output,
        )
        self.assertEqual(result.exit_code, 0)

    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.os.makedirs")
    @patch("housefire.cli.configparser.ConfigParser")
    @patch("housefire.cli.click.prompt")
    def test_init_command_creates_config_and_prompts(
        self, mock_prompt, mock_config_parser, mock_makedirs, mock_exists
    ):
        mock_exists.return_value = False
        mock_config_object = MagicMock()
        mock_config_parser.return_value = mock_config_object
        mock_prompt.side_effect = [
            "/tmp/housefire_data",
            "test_hf_key",
            "test_gmaps_key",
            "http://localhost",
            "dev",
            "/tmp/logs",
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            result = self.runner.invoke(cli.housefire, ["init"])

        self.assertIn("Creating config file at", result.output)
        mock_makedirs.assert_called()
        self.assertEqual(mock_prompt.call_count, 6)
        mock_config_object.write.assert_called_once()
        self.assertIn("Config file at", result.output)
        self.assertEqual(result.exit_code, 0)

    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.os.makedirs")
    @patch("housefire.cli.configparser.ConfigParser")
    def test_init_command_with_options(
        self, mock_config_parser, mock_makedirs, mock_exists
    ):
        mock_exists.return_value = True
        mock_config_object = MagicMock()
        mock_config_parser.return_value = mock_config_object

        with patch("builtins.open", mock_open()) as mock_file:
            result = self.runner.invoke(
                cli.housefire,
                [
                    "init",
                    "--temp-dir-path",
                    "/tmp/data",
                    "--housefire-api-key",
                    "hf_key",
                    "--google-maps-api-key",
                    "gmaps_key",
                    "--housefire-base-url",
                    "http://test.com",
                    "--deploy-env",
                    "test",
                    "--log-dir-path",
                    "/tmp/test_logs",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Config file at", result.output)
        config_calls = mock_config_object.__setitem__.call_args_list
        self.assertIn(call("TEMP_DIR_PATH", "/tmp/data"), config_calls[0].args[1])

    @patch("housefire.cli.run_data_pipeline_main")
    @patch("housefire.cli.HousefireConfig")
    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.configparser.ConfigParser")
    def test_run_data_pipeline_command(
        self, mock_config_parser, mock_exists, mock_hf_config, mock_run_main
    ):
        mock_exists.return_value = True
        mock_config = MagicMock(spec=HousefireConfig)
        mock_config.temp_dir_path = "/tmp"
        mock_hf_config.return_value = mock_config

        result = self.runner.invoke(
            cli.housefire, ["run-data-pipeline", "DLR", "--save-output"]
        )

        self.assertEqual(result.exit_code, 0)
        mock_run_main.assert_called_once()

    @patch("housefire.cli.scrape_main")
    @patch("housefire.cli.HousefireConfig")
    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.configparser.ConfigParser")
    def test_scrape_command(
        self, mock_config_parser, mock_exists, mock_hf_config, mock_scrape_main
    ):
        mock_exists.return_value = True
        mock_config = MagicMock(spec=HousefireConfig)
        mock_config.temp_dir_path = "/tmp"
        mock_hf_config.return_value = mock_config

        result = self.runner.invoke(
            cli.housefire, ["scrape", "DLR", "--debug", "--save-output"]
        )

        self.assertEqual(result.exit_code, 0)
        mock_scrape_main.assert_called_once()

    @patch("housefire.cli.TransformerFactory")
    @patch("housefire.cli.GoogleGeocodeAPI")
    @patch("housefire.cli.HousefireClient")
    @patch("housefire.cli.HousefireLoggerFactory")
    @patch("housefire.cli.ScrapeResult")
    @patch("housefire.cli.TransformResult")
    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.HousefireConfig")
    @patch("housefire.cli.configparser.ConfigParser")
    def test_transform_command(
        self,
        mock_config_parser,
        mock_hf_config,
        mock_os_exists,
        mock_transform_result,
        mock_scrape_result,
        mock_logger_factory,
        mock_hf_client,
        mock_geocode_api,
        mock_transformer_factory,
    ):
        mock_os_exists.return_value = True
        mock_config = MagicMock(spec=HousefireConfig)
        mock_config.temp_dir_path = "/tmp"
        mock_config.deploy_env = "test"
        mock_config.log_dir_path = "/logs"
        mock_config.housefire_api_key = "key"
        mock_config.housefire_base_url = "url"
        mock_config.google_maps_api_key = "gkey"
        mock_hf_config.return_value = mock_config

        mock_transformer = MagicMock()
        mock_transformer_factory.return_value.get_transformer.return_value = (
            mock_transformer
        )

        with self.runner.isolated_filesystem():
            with open("test.csv", "w") as f:
                f.write("a,b,c")

            result = self.runner.invoke(
                cli.housefire,
                ["transform", "DLR", "test.csv", "--save-output"],
            )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_transformer.transform.assert_called_once()
        mock_transform_result.to_csv.assert_called_once()

    @patch("housefire.cli.HousefireClient")
    @patch("housefire.cli.TransformResult")
    @patch("housefire.cli.HousefireConfig")
    @patch("housefire.cli.os.path.exists")
    @patch("housefire.cli.configparser.ConfigParser")
    def test_upload_command(
        self,
        mock_config_parser,
        mock_exists,
        mock_hf_config,
        mock_transform_result,
        mock_hf_client,
    ):
        mock_exists.return_value = True
        mock_config = MagicMock(spec=HousefireConfig)
        mock_hf_config.return_value = mock_config
        mock_transform_result.from_csv.return_value = [
            MagicMock(spec=TransformResult, property={})
        ]

        with self.runner.isolated_filesystem():
            with open("test.csv", "w") as f:
                f.write("a,b,c")

            result = self.runner.invoke(cli.housefire, ["upload", "DLR", "test.csv"])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("uploading transformed data", result.output.lower())
        mock_hf_client.return_value.update_properties_by_ticker.assert_called_once()

    @patch("housefire.cli.os.mkdir")
    @patch("housefire.cli.uuid.uuid4")
    @patch("housefire.cli.datetime")
    def test_create_temp_dir(self, mock_datetime, mock_uuid, mock_mkdir):
        mock_uuid.return_value = "1234"
        mock_datetime.datetime.now.return_value.isoformat.return_value = (
            "2025-01-01T00:00:00"
        )

        path = cli._create_temp_dir("/base", "TICK")

        self.assertTrue(path.startswith("/base/TICK_2025-01-01T00:00:00_1234"))
        mock_mkdir.assert_called_once()

    @patch("housefire.cli.os.listdir")
    @patch("housefire.cli.os.remove")
    @patch("housefire.cli.os.rmdir")
    def test_delete_temp_dir(self, mock_rmdir, mock_remove, mock_listdir):
        mock_listdir.return_value = ["file1.txt", "file2.txt"]

        cli._delete_temp_dir("/tmp/testdir")

        self.assertEqual(mock_remove.call_count, 2)
        mock_rmdir.assert_called_with("/tmp/testdir")


if __name__ == "__main__":
    unittest.main()
