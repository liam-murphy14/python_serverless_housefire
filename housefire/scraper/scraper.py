from abc import ABC, abstractmethod
from logging import Logger
import pandas as pd
import nodriver as uc
import random as r
import time


class Scraper(ABC):

    driver: uc.Browser
    temp_dir_path: str
    ticker: str
    logger: Logger

    def __init__(self):
        pass

    @abstractmethod
    async def execute_scrape(self) -> pd.DataFrame:
        return NotImplemented

    @abstractmethod
    async def _debug_scrape(self) -> None:
        """
        debugging method to scrape data at a small scale, can be used for manual testing
        """
        pass

    async def scrape(self) -> pd.DataFrame:
        """
        Scrape data and log
        """
        self.logger.debug(f"Scraping data for REIT: {self.ticker}")
        scraped_data = await self.execute_scrape()
        self.logger.debug(f"Scraped data for REIT: {self.ticker}, df: {scraped_data}")
        return scraped_data

    def _jiggle(self):
        """
        pauses for a random amount of seconds between 10 and 70

        returns the amount of time jiggled
        """
        jiggle_time = r.randint(10, 70)
        self.logger.debug(f"Jiggling for {jiggle_time} seconds")
        time.sleep(jiggle_time)
        return jiggle_time

    def _wait(self, seconds: int):
        """
        pauses for a given amount of seconds

        returns the amount of time waited
        """
        self.logger.debug(f"Waiting for {seconds} seconds")
        time.sleep(seconds)
        return seconds





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
# # NOT CURRENTLY USED
# # TODO: start using this once nodriver is updated with experimental options
# def create_temp_dir(base_path: str) -> str:
#     """
#     Create a new directory with a random name in the temp directory
#
#     param: base_path: the path to the base directory to create the new directory in
#
#     returns: the full path to the new directory
#     """
#     dir_name = str(uuid.uuid4())
#     new_dir_path = os.path.join(base_path, dir_name)
#     self.logger.debug(f"Creating temp directory at {new_dir_path}")
#     os.mkdir(new_dir_path)
#     self.logger.info(f"Created temp directory at {new_dir_path}")
#     return new_dir_path
#
#
# # NOT CURRENTLY USED
# # TODO: start using this once nodriver is updated with experimental options
# def delete_temp_dir(temp_dir_path: str) -> None:
#     """
#     Delete a directory and all of its contents
#     USE WITH CAUTION
#
#     param: temp_dir_path: the path to the directory to delete
#     """
#     self.logger.debug(f"Deleting directory at {temp_dir_path}")
#     try:
#         for filename in os.listdir(temp_dir_path):
#             file_path = os.path.join(temp_dir_path, filename)
#             self.logger.debug(f"Deleting file at {file_path}")
#             os.remove(file_path)
#         os.rmdir(temp_dir_path)
#         self.logger.info(f"Deleted directory at {temp_dir_path}")
#     except Exception as e:
#         self.logger.error(f"Error deleting directory at {temp_dir_path}: {e}", exc_info=True)
#
#
