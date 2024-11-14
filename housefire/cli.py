import click
import nodriver as uc
import os
import uuid
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
    # skip this check if the user is running the init command
    if ctx.invoked_subcommand == "init":
        return
    if not os.path.exists(config_path):
        click.echo(
            f"Looks like there is no config file at {config_path}. Run 'housefire init' to get started."
        )
        raise SystemExit(0)
    config_object = configparser.ConfigParser()
    config_object.read(config_path)
    try:
        ctx.obj["CONFIG"] = HousefireConfig(config_object)
    except ValueError:
        click.echo(
            f"Looks like your config file at {config_path} is not initialized. Run 'housefire init' to get started."
        )
        raise SystemExit(0)


@housefire.command()
@click.option(
    "--temp-dir-path",
    help="Path to the temporary directory where scraped data will be stored.",
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

    config_object = configparser.ConfigParser()
    config_object.read(config_path)
    if "HOUSEFIRE" not in config_object:
        config_object["HOUSEFIRE"] = {}

    # set defaults
    temp_dir_path_default = "/tmp/housefire_data"
    housefire_base_url_default = "https://housefire.liammurphydev.com/api/"
    deploy_env_default = "development"

    # create temp dir if it doesn't exist
    if not os.path.exists(temp_dir_path_default):
        os.makedirs(temp_dir_path_default)

    if temp_dir_path is None or len(temp_dir_path) == 0:
        temp_dir_prompt_value = (
            config_object["HOUSEFIRE"].get("TEMP_DIR_PATH")
            if "TEMP_DIR_PATH" in config_object["HOUSEFIRE"]
            else temp_dir_path_default
        )
        temp_dir_path = click.prompt(
            f"Enter the path to the temporary directory where scraped data will be stored. Press enter to accept current value",
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
            f"Enter the Housefire API key. Press enter to accept current value",
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
            f"Enter the Google Maps API key. Press enter to accept current value",
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
            f"Enter the Housefire API base URL. Press enter to accept current value",
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
            f"Enter the deploy environment. Press enter to accept current value",
            default=deploy_env_prompt_value,
            type=str,
        )
    config_object["HOUSEFIRE"]["DEPLOY_ENV"] = deploy_env

    with open(config_path, "w") as config_file:
        config_object.write(config_file)
    click.echo(f"Config file at {config_path} has been initialized.")


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
    temp_dir_path = _create_temp_dir(config.temp_dir_path)
    logger_factory = HousefireLoggerFactory(config.deploy_env)
    scraper_factory = ScraperFactory(logger_factory, config.chrome_path, temp_dir_path)
    scraper = await scraper_factory.get_scraper(ticker)
    scraped_data = await scraper.scrape()

    housefire_api = HousefireAPI(
        logger_factory.get_logger(HousefireAPI.__name__),
        config.housefire_api_key,
        config.housefire_base_url,
    )
    geocode_api = GoogleGeocodeAPI(
        logger_factory.get_logger(GoogleGeocodeAPI.__name__),
        housefire_api,
        config.google_maps_api_key,
    )

    transformer_factory = TransformerFactory(logger_factory, geocode_api)
    transformer = transformer_factory.get_transformer(ticker)
    transformed_data = transformer.transform(scraped_data)

    housefire_api.update_properties_by_ticker(
        ticker.upper(), HousefireAPI.df_to_request(transformed_data)
    )
    _delete_temp_dir(temp_dir_path)


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
    temp_dir_path = _create_temp_dir(config.temp_dir_path)
    logger_factory = HousefireLoggerFactory(config.deploy_env)
    scraper_factory = ScraperFactory(logger_factory, config.chrome_path, temp_dir_path)
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
    _delete_temp_dir(temp_dir_path)


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


def _create_temp_dir(base_dir_path: str) -> str:
    """
    Create a new directory with a random name in the temp directory

    param: base_path: the path to the base directory to create the new directory in

    returns: the full path to the new directory
    """
    dir_name = str(uuid.uuid4())
    new_dir_path = os.path.join(base_dir_path, dir_name)
    os.mkdir(new_dir_path)
    return new_dir_path


def _delete_temp_dir(temp_dir_path: str) -> None:
    """
    Delete a directory and all of its contents
    USE WITH CAUTION

    param: temp_dir_path: the path to the directory to delete
    """
    for filename in os.listdir(temp_dir_path):
        file_path = os.path.join(temp_dir_path, filename)
        os.remove(file_path)
    os.rmdir(temp_dir_path)


# # extra stuff i dont know what to do with yet. TODO: figure out a better place for this
# # NOT CURRENTLY USED, BUT MAY BE USEFUL IN THE FUTURE
# # TODO: instead of edge config nonsese, just add these objects to the REIT table in db
# def format_edge_config_ciks():
#     CIK_ENDPOINT = "https://sec.gov/files/company_tickers.json"
#     to_concat_list = ["{"]
#     reit_csv = pd.read_csv("adsf")  # TODO: change
#     reit_set = set(reit_csv["Symbol"])
#     cik_res = r.get(CIK_ENDPOINT)
#     cik_data = cik_res.json()
#     for key in cik_data:
#         cik_str, ticker = str(cik_data[key]["cik_str"]), cik_data[key]["ticker"]
#         if ticker not in reit_set:
#             continue
#         cik_str = cik_str.zfill(10)
#         to_concat_list.append(f'     "{ticker}": "{cik_str}",')
#     to_concat_list.append("}")
#     return "\n".join(to_concat_list)
#
#
