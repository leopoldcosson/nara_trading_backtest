# backtesting/strategy.py
import pandas as pd
import copy
from typing import List, Type

class Strategy:
    def __init__(self, name: str, data: pd.DataFrame):
        """
        Initialize a Strategy instance.

        Parameters:
        name (str): The name of the strategy.
        data (pd.DataFrame): The data to be used by the strategy.
        """
        self.strategy_name = name
        self.data = copy.deepcopy(data)

    def calculate_signal(self) -> None:
        """
        Calculate the trading signal.

        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method")

    def calculate_positions(self) -> pd.DataFrame:
        """
        Calculate the trading positions.

        This method should be implemented by subclasses.

        Returns:
        pd.DataFrame: A DataFrame containing the calculated positions.
        """
        raise NotImplementedError("Subclasses should implement this method")


class StrategyManager:
    def __init__(self, strategies: List[Type[Strategy]]):
        """
        Initialize a StrategyManager instance.

        Parameters:
        strategies (List[Type[Strategy]]): A list of Strategy instances.
        """
        self.strategies = strategies

    def calculate_all_signals(self) -> None:
        """
        Calculate signals for all strategies.
        """
        for strategy in self.strategies:
            strategy.calculate_signal()

    def calculate_all_positions(self) -> pd.DataFrame:
        """
        Calculate positions for all strategies and combine them into a single DataFrame.

        Returns:
        pd.DataFrame: A DataFrame containing the combined positions from all strategies.
        """
        all_positions = pd.DataFrame()
        for strategy in self.strategies:
            positions = strategy.calculate_positions()
            all_positions = pd.concat([all_positions, positions], axis=0)
        all_positions = all_positions.loc[:, ~all_positions.columns.duplicated()]
        return all_positions
