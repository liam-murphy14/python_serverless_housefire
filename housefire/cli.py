import click
import nodriver as uc
import os
import configparser

from housefire.dependency.google_maps import GoogleGeocodeAPI
from housefire.dependency.housefire_api import HousefireAPI
from housefire.logger import HousefireLoggerFactory
from housefire.scraper.scraper_factory import ScraperFactory
from housefire.transformer.transformer_factory import TransformerFactory
from housefire.config import HousefireConfig


def main():
    housefire(obj={})


@click.group()
@click.option(
    "--config-path",
    default=f"{os.getenv('HOME')}/.config/housefire/default.ini",
    help="Path to the config file.",
    type=click.Path(
        dir_okay=False,
        exists=False,
        resolve_path=True,
        readable=True,
        writable=True,
        allow_dash=False,
    ),
)
@click.pass_context
def housefire(ctx, config_path: str):
    """
    Housefire CLI for scraping and uploading property data.
    """
    ctx.ensure_object(dict)
    ctx.obj["CONFIG_PATH"] = config_path
    if not os.path.exists(config_path):
        click.echo(
            f"Looks like there is no config file at {config_path}. Run 'housefire init' to get started."
        )
        return
    # TODO: make sure this won't write an empty file
    with open(config_path, "r") as configfile:
        config_object = configparser.ConfigParser()
        config_object.read(configfile)
        try:
            ctx.obj["CONFIG"] = HousefireConfig(config_object)
        except ValueError:
            click.echo(
            f"Looks like your config file at {config_path} is not initialized. Run 'housefire init' to get started."
)
            return
        


@housefire.command()
@click.option(
    "--temp-dir-path",
    help="WARNING: must be the default folder that Google Chrome downloads to in order for download-based scrapers to work properly. Path to the temporary directory where scraped data will be stored.",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        resolve_path=True,
        readable=True,
        writable=True,
        allow_dash=False,
    ),
)
@click.option("--housefire-api-key", help="Housefire API key.", type=str)
@click.option("--google-maps-api-key", help="Google Maps API key.", type=str)
@click.option("--housefire-base-url", help="Housefire API base URL.", type=str)
@click.option("--deploy-env", help="Housefire API base URL.", type=str)
@click.pass_context
def init(
    ctx,
    temp_dir_path: str,
    housefire_api_key: str,
    google_maps_api_key: str,
    housefire_base_url: str,
    deploy_env: str,
):
    """
    Initialize the housefire CLI, creating a config file if it does not already exist.
    """
    config_path = ctx.obj["CONFIG_PATH"]
    if not os.path.exists(config_path):
        click.echo(f"Creating config file at {config_path}.")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, "w") as configfile:
        config_object = configparser.ConfigParser()
        config_object.read(configfile)
        if "HOUSEFIRE" not in config_object:
            config_object["HOUSEFIRE"] = {}

        # set defaults
        temp_dir_path_default = f"{os.getenv('HOME')}/Downloads/"
        housefire_base_url_default = "https://housefire.liammurphydev.com/api/"
        deploy_env_default = "development"

        if temp_dir_path is None or len(temp_dir_path) == 0:
            temp_dir_prompt_value = (
                config_object["HOUSEFIRE"].get("TEMP_DIR_PATH")
                if "TEMP_DIR_PATH" in config_object["HOUSEFIRE"]
                else temp_dir_path_default
            )
            temp_dir_path = click.prompt(
                f"Enter the path to the temporary directory where scraped data will be stored. Press enter to accept current value=[{temp_dir_prompt_value}].",
                default=temp_dir_prompt_value,
                type=click.Path(
                    file_okay=False,
                    dir_okay=True,
                    exists=True,
                    resolve_path=True,
                    readable=True,
                    writable=True,
                    allow_dash=False,
                ),
            )
        config_object["HOUSEFIRE"]["TEMP_DIR_PATH"] = temp_dir_path

        if housefire_api_key is None or len(housefire_api_key) == 0:
            housefire_api_key_prompt_value = (
                config_object["HOUSEFIRE"].get("HOUSEFIRE_API_KEY")
                if "HOUSEFIRE_API_KEY" in config_object["HOUSEFIRE"]
                else "None"
            )
            housefire_api_key = click.prompt(
                f"Enter the Housefire API key. Press enter to accept current value=[{housefire_api_key_prompt_value}].",
                default=housefire_api_key_prompt_value,
                type=str,
            )
        config_object["HOUSEFIRE"]["HOUSEFIRE_API_KEY"] = housefire_api_key

        if google_maps_api_key is None or len(google_maps_api_key) == 0:
            google_maps_api_key_prompt_value = (
                config_object["HOUSEFIRE"].get("GOOGLE_MAPS_API_KEY")
                if "GOOGLE_MAPS_API_KEY" in config_object["HOUSEFIRE"]
                else "None"
            )
            google_maps_api_key = click.prompt(
                f"Enter the Google Maps API key. Press enter to accept current value=[{google_maps_api_key_prompt_value}].",
                default=google_maps_api_key_prompt_value,
                type=str,
            )
        config_object["HOUSEFIRE"]["GOOGLE_MAPS_API_KEY"] = google_maps_api_key

        if housefire_base_url is None or len(housefire_base_url) == 0:
            housefire_base_url_prompt_value = (
                config_object["HOUSEFIRE"].get("HOUSEFIRE_BASE_URL")
                if "HOUSEFIRE_BASE_URL" in config_object["HOUSEFIRE"]
                else housefire_base_url_default
            )
            housefire_base_url = click.prompt(
                f"Enter the Housefire API base URL. Press enter to accept current value=[{housefire_base_url_prompt_value}].",
                default=housefire_base_url_prompt_value,
                type=str,
            )
        config_object["HOUSEFIRE"]["HOUSEFIRE_BASE_URL"] = housefire_base_url

        if deploy_env is None or len(deploy_env) == 0:
            deploy_env_prompt_value = (
                config_object["HOUSEFIRE"].get("DEPLOY_ENV")
                if "DEPLOY_ENV" in config_object["HOUSEFIRE"]
                else deploy_env_default
            )
            deploy_env = click.prompt(
                f"Enter the deploy environment. Press enter to accept current value=[{deploy_env_prompt_value}].",
                default=deploy_env_prompt_value,
                type=str,
            )

        config_object.write(configfile)


@housefire.command()
@click.argument("ticker", required=True)
@click.pass_context
def run_data_pipeline(ctx, ticker: str):
    """
    Run the full data pipeline for scraping the TICKER website and uploading to housefire.
    """
    config = ctx.obj["CONFIG"]
    uc.loop().run_until_complete(run_data_pipeline_main(config, ticker))


async def run_data_pipeline_main(config: HousefireConfig, ticker: str):
    logger_factory = HousefireLoggerFactory(config.deploy_env)
    scraper_factory = ScraperFactory(logger_factory, config.chrome_path, config.temp_dir_path)
    scraper = await scraper_factory.get_scraper(ticker)
    scraped_data = await scraper.scrape()

    housefire_api = HousefireAPI(logger_factory.get_logger(HousefireAPI.__name__), config.housefire_api_key, config.housefire_base_url)
    geocode_api = GoogleGeocodeAPI(logger_factory.get_logger(GoogleGeocodeAPI.__name__), housefire_api, config.google_maps_api_key)

    transformer_factory = TransformerFactory(logger_factory, geocode_api)
    transformer = transformer_factory.get_transformer(ticker)
    transformed_data = transformer.transform(scraped_data)

    housefire_api.update_properties_by_ticker(
        ticker.upper(), HousefireAPI.df_to_request(transformed_data)
    )


@housefire.command()
@click.argument("ticker", required=True)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Run the scraper debugger function instead of the full scraper.",
)
@click.pass_context
def scrape(ctx, ticker: str, debug: bool):
    """
    Scrapes the TICKER website for property data.
    """
    config = ctx.obj["CONFIG"]
    uc.loop().run_until_complete(scrape_main(config, ticker, debug))


async def scrape_main(config: HousefireConfig, ticker: str, debug: bool):
    logger_factory = HousefireLoggerFactory(config.deploy_env)
    scraper_factory = ScraperFactory(logger_factory, config.chrome_path, config.temp_dir_path)
    scraper = await scraper_factory.get_scraper(ticker)
    if debug:
        await scraper._debug_scrape()
    else:
        click.echo(
            "This feature is not yet implemented. To test scraping on its own, use the --debug flag."
        )
        # NOT CURRENTLY USED
        # TODO: use this once i have implemented some caching/magic resilience for the scraper
        # return await scraper.scrape()


# NOT CURRENTLY USED
# TODO: implement this once i have implemented some local caching/magic resilience for the scraper and modularized the scrape and transforms to save to files separately
# @main.command()
# @click.argument("ticker", required=True)
# @click.option("--debug", default=False, is_flag=True, help="Run the transformer debugger function instead of the full transformer.")
# def transform(ticker: str, debug: bool):
#     """
#     Transforms the TICKER scraped data into a standardized format.
#     """
#     transformer_factory = TransformerFactory()
#     transformer = transformer_factory.get_transformer(ticker)
#     if debug:
#         transformer._debug_transform()
#     else:
#         click.echo("This feature is not yet implemented. To test transforming on its own, use the --debug flag.")

# TODO: write an uploader as well


