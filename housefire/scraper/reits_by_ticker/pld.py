from housefire.scraper.scraper import Scraper
import pandas as pd
import nodriver as uc
import os


class PldScraper(Scraper):
    """
    scraper for Prologis, scrapes CSV from website
    """

    def __init__(self):
        super().__init__()

    async def execute_scrape(self) -> pd.DataFrame:
        # find and click the hidden button to download the csv
        start_url = "https://www.prologis.com/property-search?at=building%3Bland%3Bland_lease%3Bland_sale%3Bspec_building&bounding_box%5Btop_left%5D%5B0%5D=-143.31501&bounding_box%5Btop_left%5D%5B1%5D=77.44197&bounding_box%5Bbottom_right%5D%5B0%5D=163.24749&bounding_box%5Bbottom_right%5D%5B1%5D=-60.98419&ms=uscustomary&lsr%5Bmin%5D=0&lsr%5Bmax%5D=9007199254740991&bsr%5Bmin%5D=0&bsr%5Bmax%5D=9007199254740991&so=metric_size_sort%2Cdesc&p=0&m=&an=0"
        tab = await self.driver.get(start_url)
        await self._wait(10)

        download_button = await tab.select("#download_results")
        if download_button is None:
            raise Exception("could not find download button")
        if not isinstance(download_button, uc.Element):
            raise Exception("could not find download button")
        await download_button.click()

        csv_download_button = await tab.select("#download_results_csv")
        if csv_download_button is None:
            raise Exception("could not find download button")
        if not isinstance(csv_download_button, uc.Element):
            raise Exception("could not find download button")
        await csv_download_button.click()
        await self._wait(10)

        file_list = list(
            filter(
                lambda filename: not filename.startswith("."),
                os.listdir(self.temp_dir_path),
            )
        )

        if len(file_list) == 0:
            raise Exception("could not find downloaded csv")

        self.logger.debug(
            f"downloaded pld csv, self.temp_dir_path: {self.temp_dir_path}, files: {file_list}"
        )

        # get the downloaded file, hacky but works
        filepath = os.path.join(self.temp_dir_path, file_list[0])
        self.logger.debug(f"reading csv file: {filepath}")
        df = pd.read_csv(filepath)
        self.logger.debug("deleting csv")
        os.remove(filepath)
        return df

    async def _debug_scrape(self):
        self.logger.debug("debug scrape")
        start_url = "https://www.prologis.com/property-search?at=building%3Bland%3Bland_lease%3Bland_sale%3Bspec_building&bounding_box%5Btop_left%5D%5B0%5D=-143.31501&bounding_box%5Btop_left%5D%5B1%5D=77.44197&bounding_box%5Bbottom_right%5D%5B0%5D=163.24749&bounding_box%5Bbottom_right%5D%5B1%5D=-60.98419&ms=uscustomary&lsr%5Bmin%5D=0&lsr%5Bmax%5D=9007199254740991&bsr%5Bmin%5D=0&bsr%5Bmax%5D=9007199254740991&so=metric_size_sort%2Cdesc&p=0&m=&an=0"
        tab = await self.driver.get(start_url)

        await self._wait(10)
        download_button = await tab.select("#download_results")
        if download_button is None:
            raise Exception("could not find download button")
        if not isinstance(download_button, uc.Element):
            raise Exception("could not find download button")
        await download_button.click()

        csv_download_button = await tab.select("#download_results_csv")
        if csv_download_button is None:
            raise Exception("could not find download button")
        if not isinstance(csv_download_button, uc.Element):
            raise Exception("could not find download button")
        await csv_download_button.click()
        await self._wait(10)

        file_list = list(
            filter(
                lambda filename: not filename.startswith("."),
                os.listdir(self.temp_dir_path),
            )
        )

        if len(file_list) == 0:
            raise Exception("could not find downloaded csv")

        self.logger.debug(
            f"downloaded pld csv, self.temp_dir_path: {self.temp_dir_path}, files: {file_list}"
        )

        # get the downloaded file, hacky but works
        filepath = os.path.join(self.temp_dir_path, file_list[0])
        self.logger.debug(f"reading csv file: {filepath}")
        df = pd.read_csv(filepath)
        self.logger.debug("deleting csv")
        os.remove(filepath)
        return df
