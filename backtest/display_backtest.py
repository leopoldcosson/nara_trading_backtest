# backtesting/display_backtest.py
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd

class DisplayBacktest:
    def __init__(self, backtest: 'Backtest'):
        """
        Initialize a DisplayBacktest instance.

        Parameters:
        backtest (Backtest): The backtest instance to be visualized.
        """
        self.backtest = backtest

    def plot_book(self, book: str, exclude_non_traded: bool = False) -> None:
        """
        Plot the prices, positions, and trades for a specific book.

        Parameters:
        book (str): The book to plot.
        exclude_non_traded (bool): Whether to exclude non-traded tickers.
        """
        # Create fig with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Select tickers to plot
        tickers = self.backtest.base_data.columns if not exclude_non_traded else self.backtest.trades[self.backtest.trades['book'] == book]['ticker'].unique().tolist()

        # Plot prices & positions
        for ticker in tickers:
            # Prices
            fig.add_trace(go.Scatter(x=self.backtest.base_data[ticker].index,
                                     y=self.backtest.base_data[ticker],
                                     mode='lines',
                                     name=f'Price {ticker}',
                                     legendgroup=ticker,
                                     hoverinfo='name+y'),
                          secondary_y=False)

        # Add scatter plots for trades
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
                                     hoverinfo='name+y'),
                          secondary_y=False)

            fig.add_trace(go.Scatter(x=ticker_trades_short['time'],
                                     y=ticker_trades_short['price'],
                                     mode='markers',
                                     marker=dict(symbol='arrow-down', color='red', size=10),
                                     name=f'Short Trades {ticker}',
                                     legendgroup=ticker,
                                     hoverinfo='name+y'),
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
