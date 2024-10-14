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

    def __init__(self):
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

        return self.transformer_map[ticker]()
