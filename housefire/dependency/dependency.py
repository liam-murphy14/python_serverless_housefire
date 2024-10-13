from abc import ABC
import pandas as pd
import requests as r

class Dependency(ABC):
    """
    Abstract class for dependencies
    """

    def __init__(self):
        pass

    def _is_error_response(self, response: r.Response) -> bool:
        return response.status_code >= 400


    @staticmethod
    def df_to_request(df: pd.DataFrame) -> list[dict]:
        """
        Convert a pandas DataFrame to a list of dictionaries
        """
        request_dict = df.to_dict(orient="records")
        return request_dict
