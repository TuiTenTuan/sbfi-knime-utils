from datetime import datetime
from typing import List
import pandas as pd

class Logger:
    """A lightweight logging utility that stores messages and supports DataFrame output."""
    
    def __init__(self):
        """Initialize an empty log storage."""
        self._log_messages: List[List] = []

    def log(self, function_name: str, message: str, is_error: bool = False) -> None:
        """
        Log a message with timestamp, function name, and error status.
        
        Args:
            function_name (str): Name of the function or context.
            message (str): Log message content.
            is_error (bool, optional): Indicates if the message is an error. Defaults to False.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log_messages.append([timestamp, function_name, message, is_error])
        print(f"{timestamp} - {function_name} -- {message}")

    def get_log_dataframe(self) -> pd.DataFrame:
        """
        Return logged messages as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame with columns ['Date', 'Function', 'Message', 'IsError'].
        """
        if not self._log_messages:
            return pd.DataFrame(columns=['Date', 'Function', 'Message', 'IsError'])
        
        df = pd.DataFrame(
            self._log_messages,
            columns=['Date', 'Function', 'Message', 'IsError']
        )
        return df.astype({
            'Date': 'string',
            'Function': 'string',
            'Message': 'string',
            'IsError': 'bool'
        })