import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class DisplayBacktest:
    def __init__(self, backtest: 'Backtest'):
        """
        Initialize a DisplayBacktest instance.

        Parameters:
        backtest (Backtest): The backtest instance to be visualized.
        """
        self.backtest = backtest
        
        # Check that 'time' is in the index
        if 'time' not in self.backtest.pnl.index.names:
            raise ValueError("The index must contain 'time'.")

        # Check that 'time' is a datetime
        if not pd.api.types.is_datetime64_any_dtype(self.backtest.pnl.index.get_level_values('time')):
            self.backtest.pnl.index = pd.to_datetime(self.backtest.pnl.index.get_level_values('time'))

    def calculate_max_drawdown(self, returns):
        cumulative = returns.cumsum()
        peak = cumulative.cummax()
        drawdown = (peak - cumulative) / peak
        max_drawdown = drawdown.max()
        return max_drawdown

    def calculate_metrics(self, returns, resample_period='Y'):
        if self.backtest.returns_type == 'additive':
            resampled_returns = returns.resample(resample_period).apply(lambda x: x.sum())
        # elif self.backtest.returns_type == 'multiplicative':
        #     resampled_returns = (returns.resample(resample_period).apply(lambda x: (1 + x).prod() - 1))

        resampled_volatility = returns.resample(resample_period).std() * np.sqrt(252)
        resampled_max_drawdown = returns.resample(resample_period).apply(self.calculate_max_drawdown)
        resampled_sharpe_ratio = resampled_returns / resampled_volatility
        metrics = {
            'PnL': resampled_returns,
            'Volatility': resampled_volatility,
            'Max Drawdown': resampled_max_drawdown,
            'Sharpe Ratio': resampled_sharpe_ratio
        }
        metrics_df = pd.DataFrame(metrics)
        metrics_df.index = metrics_df.index.to_period(resample_period).to_timestamp()
        return metrics_df

    def plot_book(self, book: str, exclude_non_traded: bool = False) -> None:
        """
        Plot the prices, positions, and trades for a specific book.

        Parameters:
        book (str): The book to plot.
        exclude_non_traded (bool): Whether to exclude non-traded tickers.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        tickers = self.backtest.base_data.columns if not exclude_non_traded else self.backtest.trades[self.backtest.trades['book'] == book]['ticker'].unique().tolist()

        for ticker in tickers:
            fig.add_trace(go.Scatter(x=self.backtest.base_data[ticker].index,
                                    y=self.backtest.base_data[ticker],
                                    mode='lines',
                                    name=f'Price {ticker}',
                                    legendgroup=ticker,
                                    hoverinfo='name+x+y'),
                        secondary_y=False)

        trades_long = self.backtest.trades[self.backtest.trades['units'] > 0]
        trades_short = self.backtest.trades[self.backtest.trades['units'] < 0]

        for ticker in tickers:
            ticker_trades_long = trades_long[(trades_long['ticker'] == ticker) & (trades_long['book'] == book)]
            ticker_trades_short = trades_short[(trades_short['ticker'] == ticker) & (trades_short['book'] == book)]

            fig.add_trace(go.Scatter(x=ticker_trades_long['time'],
                                    y=ticker_trades_long['price'],
                                    mode='markers',
                                    marker=dict(symbol='arrow-up', color='green', size=10),
                                    name=f'Long Trades {ticker}',
                                    legendgroup=ticker,
                                    hoverinfo='name+x+y',
                                    hovertemplate='%{x|%Y-%m-%d} - Price: %{y}'),
                        secondary_y=False)

            fig.add_trace(go.Scatter(x=ticker_trades_short['time'],
                                    y=ticker_trades_short['price'],
                                    mode='markers',
                                    marker=dict(symbol='arrow-down', color='red', size=10),
                                    name=f'Short Trades {ticker}',
                                    legendgroup=ticker,
                                    hoverinfo='name+x+y',
                                    hovertemplate='%{x|%Y-%m-%d} - Price: %{y}'),
                        secondary_y=False)

        fig.update_layout(title=f'{book}',
                        xaxis_title='Time',
                        yaxis_title='Price',
                        yaxis2_title='Position')

        fig.show()

    def plot_cumulative_pnl_per_book(self) -> None:
        """
        Plot the cumulative PnL for each book.
        """
        cumulative_pnl_book = self.backtest.compute_cumulative_pnl_book().reset_index()
        fig = go.Figure()

        for book in cumulative_pnl_book.columns[1:]:
            fig.add_trace(go.Scatter(x=cumulative_pnl_book['time'],
                                     y=cumulative_pnl_book[book],
                                     mode='lines',
                                     name=f'Book {book}'))

        fig.update_layout(title='Cumulative PnL per Book',
                          xaxis_title='Time',
                          yaxis_title='Cumulative PnL')
        fig.show()

    def plot_cumulative_pnl(self) -> None:
        """
        Plot the cumulative PnL.
        """
        cumulative_pnl = self.backtest.compute_cumulative_pnl().reset_index()
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=cumulative_pnl['time'],
                                 y=cumulative_pnl['pnl'],
                                 mode='lines',
                                 name='Cumulative PnL'))

        fig.update_layout(title='Cumulative PnL',
                          xaxis_title='Time',
                          yaxis_title='Cumulative PnL')
        fig.show()

    def plot_individual_pnl(self) -> None:
        """
        Plot the individual PnL for each book.
        """
        pnl = self.backtest.pnl.reset_index()
        fig = go.Figure()

        for book in pnl['book'].unique():
            book_data = pnl[pnl['book'] == book]
            fig.add_trace(go.Scatter(x=book_data['time'],
                                     y=book_data['pnl'],
                                     mode='lines',
                                     name=f'Book {book}'))

        fig.update_layout(title='Individual PnL per Book',
                          xaxis_title='Time',
                          yaxis_title='PnL')
        fig.show()

    def plot_pnl_distribution(self) -> None:
        """
        Plot the distribution of PnL for each strategy.
        """
        pnl = self.backtest.pnl.reset_index()
        fig = go.Figure()

        for book in pnl['book'].unique():
            book_data = pnl[pnl['book'] == book]
            fig.add_trace(go.Histogram(x=book_data['pnl'],
                                       name=f'Book {book}',
                                       opacity=0.75))

        fig.update_layout(barmode='overlay',
                          title='PnL Distribution per Book',
                          xaxis_title='PnL',
                          yaxis_title='Frequency')
        fig.show()

    def get_metrics(self, book='all', resample_period='Y'):
        """
        Get the calculated metrics for a given resample period and a given book.

        Parameters:
        book (str): The book to get the metrics for. If 'all', then calculate metrics for the whole system.
        resample_period (str): The period to resample data. Examples: 'Y' for yearly, 'M' for monthly, 'W' for weekly, 'D' for daily.

        Returns:
        DataFrame: A DataFrame containing the metrics.
        """
        if book == 'all':
            # Calculate metrics for the entire system
            returns = self.backtest.compute_pnl()['pnl']
        else:
            # Calculate metrics for a specific book
            returns = self.backtest.compute_pnl_book()[book]

        # Calculate metrics based on the resample period
        metrics_df = self.calculate_metrics(returns, resample_period=resample_period)

        return metrics_df
