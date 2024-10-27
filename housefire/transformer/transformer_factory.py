from housefire.dependency.google_maps import GoogleGeocodeAPI
from housefire.logger import HousefireLoggerFactory
from housefire.transformer.geocode_transformer import GeocodeTransformer
from housefire.transformer.reits_by_ticker.pld import PldTransformer
from housefire.transformer.reits_by_ticker.spg import SpgTransformer
from housefire.transformer.reits_by_ticker.dlr import DlrTransformer
from housefire.transformer.reits_by_ticker.well import WellTransformer
from housefire.transformer.reits_by_ticker.eqix import EqixTransformer
from housefire.transformer.transformer import Transformer


class TransformerFactory:
    """
    Factory class for creating Transformer instances
    """

    def __init__(
        self,
        logger_factory: HousefireLoggerFactory,
        geocode_api_client: GoogleGeocodeAPI,
    ):
        self.logger_factory = logger_factory
        self.google_geocode_api_client = geocode_api_client
        self.transformer_map = {
            "pld": PldTransformer,
            "spg": SpgTransformer,
            "dlr": DlrTransformer,
            "well": WellTransformer,
            "eqix": EqixTransformer,
        }

    def get_transformer(self, ticker: str) -> Transformer:
        """
        Get a new instance of a Transformer subclass
        """
        if ticker not in self.transformer_map:
            raise ValueError(f"Unsupported ticker: {ticker}")

        transformer = self.transformer_map[ticker]()
        transformer.ticker = ticker
        transformer.logger = self.logger_factory.get_logger(
            transformer.__class__.__name__
        )
        if isinstance(transformer, GeocodeTransformer):
            transformer.google_geocode_api_client = self.google_geocode_api_client
        return transformer
