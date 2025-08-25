import datetime
import pathlib
import click
import nodriver as uc
import os
import uuid
import configparser

from housefire.dependency.google_maps import GoogleGeocodeAPI
from housefire.dependency.housefire_client.client import HousefireClient
from housefire.logger import HousefireLoggerFactory
from housefire.scraper.scraper_factory import ScraperFactory
from housefire.scraper.scraper import ScrapeResult
from housefire.transformer.transformer import TransformResult
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
@click.option(
    "--log-dir-path",
    help="Path to the log directory where logs will be stored.",
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
@click.pass_context
def init(
    ctx,
    temp_dir_path: str,
    housefire_api_key: str,
    google_maps_api_key: str,
    housefire_base_url: str,
    deploy_env: str,
    log_dir_path: str,  # New parameter
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
    deploy_env_default = "production"
    log_dir_path_default = "/tmp/housefire_logs"

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

    if log_dir_path is None or len(log_dir_path) == 0:
        log_dir_path_prompt_value = (
            config_object["HOUSEFIRE"].get("LOG_DIR_PATH")
            if "LOG_DIR_PATH" in config_object["HOUSEFIRE"]
            else log_dir_path_default
        )
        log_dir_path = click.prompt(
            f"Enter the path to the log directory where logs will be stored. Press enter to accept current value",
            default=log_dir_path_prompt_value,
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
    config_object["HOUSEFIRE"]["LOG_DIR_PATH"] = log_dir_path

    with open(config_path, "w") as config_file:
        config_object.write(config_file)
    click.echo(f"Config file at {config_path} has been initialized.")


@housefire.command()
@click.argument("ticker", required=True)
@click.option(
    "--save-output",
    default=False,
    is_flag=True,
    help="Whether to save the temporary directory after the data pipeline has run.",
)
@click.pass_context
def run_data_pipeline(ctx, ticker: str, save_output: bool):
    """
    Run the full data pipeline for scraping the TICKER website and uploading to housefire.
    """
    config: HousefireConfig = ctx.obj["CONFIG"]
    # create temp dir if it doesn't exist
    if not os.path.exists(config.temp_dir_path):
        os.makedirs(config.temp_dir_path)

    uc.loop().run_until_complete(run_data_pipeline_main(config, ticker, save_output))


async def run_data_pipeline_main(
    config: HousefireConfig, ticker: str, save_output: bool
):
    temp_dir_path = _create_temp_dir(config.temp_dir_path, ticker)
    logger_factory = HousefireLoggerFactory(config.deploy_env, config.log_dir_path)

    # scrape
    scraper_factory = ScraperFactory(logger_factory, config.chrome_path)
    scraper = await scraper_factory.get_scraper(ticker, temp_dir_path)
    scraped_data = await scraper.scrape()

    if save_output:
        path = os.path.join(temp_dir_path, f"{ticker}_scraped.csv")
        ScrapeResult.to_csv(scraped_data, pathlib.Path(path))

    # initialize dependencies
    housefire_api = HousefireClient(config.housefire_api_key, config.housefire_base_url)
    geocode_api = GoogleGeocodeAPI(
        logger_factory.get_logger(GoogleGeocodeAPI.__name__),
        housefire_api,
        config.google_maps_api_key,
    )

    # transform
    transformer_factory = TransformerFactory(logger_factory, geocode_api)
    transformer = transformer_factory.get_transformer(ticker)
    transformed_data = transformer.transform(scraped_data)

    if save_output:
        path = os.path.join(temp_dir_path, f"{ticker}_transformed.csv")
        TransformResult.to_csv(transformed_data, pathlib.Path(path))

    # upload
    housefire_api.update_properties_by_ticker(
        ticker.upper(), [d.property for d in transformed_data]
    )
    if not save_output:
        _delete_temp_dir(temp_dir_path)


@housefire.command()
@click.argument("ticker", required=True)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Run the scraper debugger function instead of the full scraper.",
)
@click.option(
    "--save-output",
    default=False,
    is_flag=True,
    help="Whether to save the temporary directory after the scraper has run.",
)
@click.pass_context
def scrape(ctx, ticker: str, debug: bool, save_output: bool):
    """
    Scrapes the TICKER website for property data.
    """
    config: HousefireConfig = ctx.obj["CONFIG"]
    # create temp dir if it doesn't exist
    if not os.path.exists(config.temp_dir_path):
        os.makedirs(config.temp_dir_path)
    uc.loop().run_until_complete(scrape_main(config, ticker, debug, save_output))


async def scrape_main(
    config: HousefireConfig, ticker: str, debug: bool, save_output: bool
):
    temp_dir_path = _create_temp_dir(config.temp_dir_path, ticker)
    logger_factory = HousefireLoggerFactory(config.deploy_env, config.log_dir_path)
    scraper_factory = ScraperFactory(logger_factory, config.chrome_path)
    scraper = await scraper_factory.get_scraper(ticker, temp_dir_path)
    if debug:
        data = await scraper._debug_scrape()
    else:
        data = await scraper.scrape()
    if save_output:
        path = os.path.join(temp_dir_path, f"{ticker}_scraped.csv")
        ScrapeResult.to_csv(data, pathlib.Path(path))
        click.echo(f"Scraped data saved to {path}")
    else:
        _delete_temp_dir(temp_dir_path)
        click.echo(f"Temporary directory {temp_dir_path} deleted after scraping.")


@housefire.command()
@click.argument("ticker", required=True)
@click.argument(
    "csv-input-path",
    required=True,
    type=click.Path(
        exists=True,
        dir_okay=False,
        resolve_path=True,
        readable=True,
        writable=False,
        allow_dash=True,
    ),
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Run the transformer debugger function instead of the full transformer.",
)
@click.option(
    "--save-output",
    default=False,
    is_flag=True,
    help="Whether to save the transformation output.",
)
@click.pass_context
def transform(ctx, ticker: str, csv_input_path: str, debug: bool, save_output: bool):
    """
    Transforms the TICKER scraped data into a standardized format.
    """
    config: HousefireConfig = ctx.obj["CONFIG"]
    # create temp dir if it doesn't exist
    if not os.path.exists(config.temp_dir_path):
        os.makedirs(config.temp_dir_path)
    logger_factory = HousefireLoggerFactory(config.deploy_env, config.log_dir_path)
    housefire_api = HousefireClient(config.housefire_api_key, config.housefire_base_url)
    geocode_api = GoogleGeocodeAPI(
        logger_factory.get_logger(GoogleGeocodeAPI.__name__),
        housefire_api,
        config.google_maps_api_key,
    )
    transformer_factory = TransformerFactory(logger_factory, geocode_api)
    transformer = transformer_factory.get_transformer(ticker)
    csv_path = pathlib.Path(csv_input_path)
    click.echo(f"Reading scraped data from {csv_path}")
    data: list[ScrapeResult] = ScrapeResult.from_csv(csv_path)
    if debug:
        transformed_data = transformer._debug_transform(data)
    else:
        transformed_data = transformer.transform(data)
    if save_output:
        temp_dir_path = _create_temp_dir(config.temp_dir_path, ticker)
        output_path = os.path.join(temp_dir_path, f"{ticker}_transformed.csv")
        TransformResult.to_csv(transformed_data, pathlib.Path(output_path))
        click.echo(f"Transformed data saved to {output_path}")


@housefire.command()
@click.argument("ticker", required=True)
@click.argument(
    "csv-input-path",
    required=True,
    type=click.Path(
        exists=True,
        dir_okay=False,
        resolve_path=True,
        readable=True,
        writable=False,
        allow_dash=True,
    ),
)
@click.pass_context
def upload(ctx, ticker: str, csv_input_path: str):
    """
    Uploads the transformed TICKER data from a CSV file to the Housefire API.
    """
    config: HousefireConfig = ctx.obj["CONFIG"]
    housefire_api = HousefireClient(config.housefire_api_key, config.housefire_base_url)

    csv_path = pathlib.Path(csv_input_path)
    click.echo(f"Uploading transformed data from {csv_path} to Housefire API.")

    data: list[TransformResult] = TransformResult.from_csv(csv_path)
    housefire_api.update_properties_by_ticker(
        ticker.upper(), [d.property for d in data]
    )
    click.echo(f"Data for {ticker} uploaded successfully.")


def _create_temp_dir(base_dir_path: str, ticker: str) -> str:
    """
    Create a new directory with a random name in the temp directory

    param: base_path: the path to the base directory to create the new directory in

    returns: the full path to the new directory
    """
    dir_name = "_".join(
        (ticker, datetime.datetime.now().isoformat(), str(uuid.uuid4()))
    )
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
