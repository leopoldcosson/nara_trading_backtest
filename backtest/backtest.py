# backtesting/backtest.py
import pandas as pd
import copy
from tqdm import trange
from typing import List, Type, Dict
from .strategy import Strategy, StrategyManager

class Backtest:

    def __init__(self, base_data: pd.DataFrame, strategies: List[Type[Strategy]], signals: pd.DataFrame = None, weights: Dict[str, float] = {}, initial_cash: float = 1000000, returns_type: str = 'additive'):
        """
        Initialize a Backtest instance.

        Parameters:
        base_data (pd.DataFrame): The base data to be used for the backtest.
        strategies (List[Type[Strategy]]): A list of Strategy instances.
        signals (pd.DataFrame): The signals to be used for the backtest.
        weights (Dict[str, float]): A dictionary of weights for each strategy. Default is equal weight.
        initial_cash (float): The initial cash amount.
        returns_type (str): How returns are computed [non-implemented yet]
        """
        
        # Deep copy of the base data to avoid modifying the original data
        self.base_data = copy.deepcopy(base_data)
        
        # DataFrames to store trades, positions, PnL, and cash history
        self.trades = pd.DataFrame(columns=['time', 'book', 'ticker', 'price', 'units'])
        self.positions = pd.DataFrame(columns=['time', 'book', 'ticker', 'units'])
        self.pnl = pd.DataFrame(columns=['time', 'book', 'ticker', 'pnl'])
        self.cumulative_pnl = pd.DataFrame(columns=['time', 'book', 'pnl'])
        self.cash_history = pd.DataFrame(columns=['time', 'cash'])
        
        # Generator for incrementally processing the base data
        self.data_generator = self._data_generator()
        
        # Handling signals if provided
        self.base_signals = signals
        if self.base_signals is not None:
            self.signal_generator = self._signals_generator()
        
        # Initialize StrategyManager with the provided strategies
        self.strategy_manager = StrategyManager(strategies)
        
        # DataFrame to store the next positions
        self.next_positions = pd.DataFrame(columns=['time', 'ticker', 'units'])
        
        # Setting up strategy weights, defaulting to equal weights if not provided
        self.weights = weights if weights else {strategy.strategy_name: 1 for strategy in strategies}
        
        # Initialize cash-related attributes
        self.initial_cash = initial_cash
        self.cash = initial_cash
        
        # Type of returns computation (additive or multiplicative)
        self.returns_type = returns_type
        
        # Run the backtest
        self.run_backtest()

    def _data_generator(self) -> pd.DataFrame:
        """
        Generator to yield the base data incrementally with trange.

        Yields:
        pd.DataFrame: The incremental base data.
        """
        for i in trange(1, len(self.base_data) + 1):
            yield self.base_data.iloc[:i]

    def _signals_generator(self) -> pd.DataFrame:
        """
        Generator to yield the signals incrementally without trange.

        Yields:
        pd.DataFrame: The incremental signals data.
        """
        for i in range(1, len(self.base_signals) + 1):
            yield self.base_signals.iloc[:i]

    def next(self) -> bool:
        """
        Get the next incremental data.

        Returns:
        bool: True if there is more data, False otherwise.
        """
        try:
            self.data = next(self.data_generator)
            if self.base_signals is not None:
                self.signal = next(self.signal_generator)
            return True
        except StopIteration:
            return False

    def update_pnl(self) -> None:
        """
        Update the PnL based on the latest and penultimate positions.
        """
        if len(self.data) > 3:
            latest_date = self.data.index[-2]
            penultimate_date = self.data.index[-3]
            latest_positions = self.positions[self.positions['time'] == penultimate_date]
            for book in latest_positions['book'].unique():
                for ticker in latest_positions['ticker'].unique():
                    latest_prices = self.data.loc[latest_date, ticker]
                    penultimate_prices = self.data.loc[penultimate_date, ticker]
                    if self.returns_type == 'additive':
                        diff = latest_prices - penultimate_prices
                    # elif self.returns_type == 'multiplicative':
                    #     diff = (latest_prices / penultimate_prices) - 1
                    new_pnl = pd.DataFrame([[latest_date, book, ticker, diff * latest_positions.loc[(latest_positions['ticker'] == ticker) & (latest_positions['book'] == book), 'units'].values[0]]], columns=self.pnl.columns)
                    self.pnl = pd.concat([self.pnl, new_pnl], ignore_index=True)

    def update_positions_and_trades(self) -> None:
        """
        Update positions and trades based on the latest and penultimate positions.
        """
        if len(self.data) > 3:
            latest_date = self.data.index[-2]
            penultimate_date = self.data.index[-3]
            latest_positions = self.next_positions[self.next_positions['time'] == latest_date]
            penultimate_positions = self.positions[self.positions['time'] == penultimate_date]
            for index, row in latest_positions.iterrows():
                book = row['book']
                ticker = row['ticker']
                units = row['units']
                if not penultimate_positions.empty:
                    penultimate_units = penultimate_positions.loc[(penultimate_positions['ticker'] == ticker) & (penultimate_positions['book'] == book), 'units'].values
                    penultimate_units = penultimate_units[0] if len(penultimate_units) > 0 else 0
                else:
                    penultimate_units = 0
                trade_units = units - penultimate_units
                if trade_units != 0:
                    trade_price = self.data.loc[latest_date, ticker]
                    self.add_trade(latest_date, book, ticker, trade_price, trade_units)
                self.update_position(latest_date, book, ticker, units)

    def run_strategies(self) -> None:
        """
        Run all strategies to calculate signals and positions.
        """
        self.strategy_manager.update_all_datas(self.data)
        if self.base_signals is not None:
            self.strategy_manager.update_all_signals(self.signal)
        self.strategy_manager.calculate_all_signals()
        self.next_positions = self.strategy_manager.calculate_all_positions()

    def run_backtest(self) -> None:
        """
        Run the backtest.
        """
        # Iterate through the data incrementally
        while self.next():
            # Update Profit and Loss (PnL) based on the latest data
            self.update_pnl()
            
            # Update positions and trades with the most recent data
            self.update_positions_and_trades()
            
            # Execute all strategies to calculate new signals and positions
            self.run_strategies()
            
            # Update the cash balance based on the latest PnL
            self.update_cash()
        
        # Set the 'time' column as the index for the PnL DataFrame
        self.pnl.set_index('time', inplace=True)

    def add_trade(self, time: pd.Timestamp, book: str, ticker: str, buy_price: float, units: float) -> None:
        """
        Add a trade to the trades DataFrame.

        Parameters:
        time (pd.Timestamp): The time of the trade.
        book (str): The book of the trade.
        ticker (str): The ticker of the trade.
        buy_price (float): The price of the trade.
        units (float): The units of the trade.
        """
        new_trade = pd.DataFrame([[time, book, ticker, buy_price, units]], columns=self.trades.columns)
        self.trades = pd.concat([self.trades, new_trade], ignore_index=True)

    def update_position(self, time: pd.Timestamp, book: str, ticker: str, units: float) -> None:
        """
        Update the positions DataFrame.

        Parameters:
        time (pd.Timestamp): The time of the position.
        book (str): The book of the position.
        ticker (str): The ticker of the position.
        units (float): The units of the position.
        """
        if not ((self.positions['book'] == book) & (self.positions['ticker'] == ticker) & (self.positions['time'] == time)).any():
            new_position = pd.DataFrame([[time, book, ticker, units]], columns=self.positions.columns)
            self.positions = pd.concat([self.positions, new_position], ignore_index=True)
        else:
            self.positions.loc[(self.positions['book'] == book) & (self.positions['ticker'] == ticker) & (self.positions['time'] == time), 'units'] = units

    def update_cash(self) -> None:
        """
        Update the cash variable based on the latest PnL.
        """
        if len(self.pnl) > 2:
            latest_date = self.data.index[-2]

            # Compute the weighted PnL
            if self.weights:
                weighted_pnl = 0
                for book, weight in self.weights.items():
                    book_pnl = self.pnl[(self.pnl['time'] == latest_date) & (self.pnl['book'] == book)]['pnl'].sum()
                    weighted_pnl += book_pnl * weight
            else:
                weighted_pnl = self.pnl[self.pnl['time'] == latest_date]['pnl'].sum()

            self.cash += weighted_pnl
            new_cash_entry = pd.DataFrame([[latest_date, self.cash]], columns=['time', 'cash'])
            self.cash_history = pd.concat([self.cash_history, new_cash_entry], ignore_index=True)


    def compute_pnl_book(self) -> pd.DataFrame:
        """
        Compute the PnL for each book.

        Returns:
        pd.DataFrame: The PnL for each book.
        """
        return self.pnl.groupby(['time', 'book'])['pnl'].sum().unstack()

    def compute_cumulative_pnl_book(self) -> pd.DataFrame:
        """
        Compute the cumulative PnL for each book.

        Returns:
        pd.DataFrame: The cumulative PnL for each book.
        """
        return self.pnl.groupby(['time', 'book'])['pnl'].sum().groupby(level=1).cumsum().unstack()

    def compute_pnl(self) -> pd.DataFrame:
        """
        Compute the weighted PnL.

        Returns:
        pd.DataFrame: The weighted PnL.
        """
        pnl = self.pnl.copy()
        for book, weight in self.weights.items():
            pnl.loc[pnl['book'] == book, 'pnl'] *= weight
        return pnl.groupby('time')[['pnl']].sum()

    def compute_cumulative_pnl(self) -> pd.DataFrame:
        """
        Compute the cumulative weighted PnL.

        Returns:
        pd.DataFrame: The cumulative weighted PnL.
        """
        pnl = self.compute_pnl()
        return pnl[['pnl']].cumsum()

    def export_excel(self, filename: str = "backtest_results.xlsx") -> None:
        """
        Export the backtest results to an Excel file.

        Parameters:
        filename (str): The name of the Excel file.
        """
        with pd.ExcelWriter(filename) as writer:
            self.base_data.to_excel(writer, sheet_name='Prices', index=True)
            self.positions.to_excel(writer, sheet_name='Positions', index=False)
            self.trades.to_excel(writer, sheet_name='Trades', index=False)
            pnl_ticker = self.pnl.pivot_table(index='time', columns='ticker', values='pnl', aggfunc='sum')
            pnl_ticker.columns = [f'PnL_{col}' for col in pnl_ticker.columns]
            pnl_book = self.compute_pnl_book()
            pnl_book.columns = [f'PnL_{col}' for col in pnl_book.columns]
            cumulative_pnl_book = self.compute_cumulative_pnl_book()
            cumulative_pnl_book.columns = [f'Cumulative_PnL_{col}' for col in cumulative_pnl_book.columns]
            cumulative_pnl = self.compute_cumulative_pnl()
            cumulative_pnl.columns = ['Cumulative_PnL']
            pnl_df = pnl_ticker.join(pnl_book).join(cumulative_pnl_book).join(cumulative_pnl)
            pnl_df.to_excel(writer, sheet_name='PnL')
            for strategy in self.strategy_manager.strategies:
                book_position = self.positions[self.positions['book'] == strategy.strategy_name].pivot_table(index='time', columns='ticker', values='units', aggfunc='sum')
                strategy_sheet = self.base_data.loc[:, self.base_data.columns.isin(book_position.columns.to_list())]
                strategy_sheet = strategy_sheet.join(book_position, rsuffix='_Position')
                strategy_sheet = strategy_sheet.join(pnl_book[[f'PnL_{strategy.strategy_name}']])
                strategy_sheet = strategy_sheet.join(cumulative_pnl_book[[f'Cumulative_PnL_{strategy.strategy_name}']])
                strategy_sheet.to_excel(writer, sheet_name=strategy.strategy_name)
            if self.base_signals is not None:
                self.base_signals.to_excel(writer, sheet_name='Signals', index=True)
            self.cash_history.to_excel(writer, sheet_name='Cash', index=False)
        print(f'Backtest results exported to {filename}')