
# Nara Backtesting Platform

The Nara Backtesting Platform is a comprehensive framework designed for backtesting algorithmic trading strategies. It provides a robust set of tools to help you develop, test, and visualize your trading strategies. This package includes:

- A base class for defining strategies.
- A strategy manager to handle multiple strategies.
- A backtest engine to simulate trading based on historical data.
- Visualization tools to analyze the performance of your strategies.

## Features

- **Strategy Definition**: Define your own trading strategies by extending the base Strategy class.
- **Strategy Management**: Manage multiple strategies simultaneously using the StrategyManager.
- **Backtesting**: Run backtests to evaluate the performance of your strategies on historical data.
- **Visualization**: Generate plots to visualize prices, positions, trades, and PnL for each strategy.
- **Metrics Calculation**: Calculate performance metrics such as PnL, volatility, max drawdown, and Sharpe ratio.
- **Export Results**: Export backtest results to an Excel file for further analysis.

## Installation

To use the Nara Backtesting Platform, you need to install the required package using pip:

```bash
pip install backtesting-package
```

## Usage

### Define Your Strategies

To define a new strategy, extend the Strategy base class and implement the calculate_signal and calculate_positions methods. Here is an example of a simple moving average strategy:

```python
from backtest import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, name, tickers, short_window, long_window):
        """
        Initialize the MovingAverageStrategy with specified parameters.

        Parameters:
        name (str): The name of the strategy.
        tickers (list): List of ticker symbols.
        short_window (int): The window size for the short moving average.
        long_window (int): The window size for the long moving average.
        """
        super().__init__(name)
        self.tickers = tickers
        self.short_window = short_window
        self.long_window = long_window

    def calculate_signal(self):
        """
        Calculate the signals for each ticker based on moving averages.
        """
        for ticker in self.tickers:
            # Calculate short and long moving averages
            self.data[f'{self.strategy_name}_{ticker}_short_ma'] = self.data[ticker].rolling(window=self.short_window).mean()
            self.data[f'{self.strategy_name}_{ticker}_long_ma'] = self.data[ticker].rolling(window=self.long_window).mean()
            self.data[f'{self.strategy_name}_{ticker}_signal'] = 0.0
            
            # Generate signals where the short MA is greater than the long MA
            valid_index = self.data.index[self.short_window:]  # Valid index for slicing
            self.data.loc[valid_index, f'{self.strategy_name}_{ticker}_signal'] = np.where(
                self.data.loc[valid_index, f'{self.strategy_name}_{ticker}_short_ma'] > self.data.loc[valid_index, f'{self.strategy_name}_{ticker}_long_ma'], 1.0, 0.0
            )

    def calculate_positions(self):
        """
        Calculate positions based on the signals.

        Returns:
        pd.DataFrame: DataFrame containing the positions for each ticker at the last date.
        """
        positions_list = []
        last_date = self.data.index[-1]
        for ticker in self.tickers:
            positions = pd.DataFrame({
                'time': [last_date],
                'book': self.strategy_name,
                'ticker': ticker,
                'units': np.where(self.data.loc[last_date, f'{self.strategy_name}_{ticker}_signal'] == 1.0, 10, -10)
            })
            positions_list.append(positions)
        return pd.concat(positions_list)
```

### Signals

Instead of calculating your signals at each iteration within the strategy, you can compute them at the beginning and use them as needed throughout your strategy. Please note that your signals will be available to your strategy only up to the current date of iteration. Ensure that you do not compute them using future data (e.g., fitting a regression on the entire dataset and then iterating over it as if it were a signal).

#### Define your signals

```python
# Calculate moving averages and signals
signals = pd.DataFrame(index=data.index)

for ticker in tickers:
    signals[f'StrategyShortMA_{ticker}_short_ma'] = data[ticker].rolling(window=5).mean()
    signals[f'StrategyShortMA_{ticker}_long_ma'] = data[ticker].rolling(window=21).mean()
    signals[f'StrategyLongMA_{ticker}_short_ma'] = data[ticker].rolling(window=20).mean()
    signals[f'StrategyLongMA_{ticker}_long_ma'] = data[ticker].rolling(window=50).mean()

# Display
signals.plot()
```

#### Define your strategy

```python
from backtest import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, name, tickers, short_window, long_window):
        """
        Initialize the MovingAverageStrategy with specified parameters.

        Parameters:
        name (str): The name of the strategy.
        tickers (list): List of ticker symbols.
        short_window (int): The window size for the short moving average.
        long_window (int): The window size for the long moving average.
        """
        super().__init__(name)
        self.tickers = tickers
        self.short_window = short_window
        self.long_window = long_window

    def calculate_signal(self):
        """
        Calculate the signals for each ticker using precomputed moving averages from self.signals.
        """
        for ticker in self.tickers:
            short_ma_column = f'{self.strategy_name}_{ticker}_short_ma'
            long_ma_column = f'{self.strategy_name}_{ticker}_long_ma'
            self.data[f'{self.strategy_name}_{ticker}_signal'] = 0.0
            
            # Generate signals where the short MA is greater than the long MA
            valid_index = self.data.index[self.short_window:]  # Valid index for slicing
            self.data.loc[valid_index, f'{self.strategy_name}_{ticker}_signal'] = np.where(
                self.signal.loc[valid_index, short_ma_column] > self.signal.loc[valid_index, long_ma_column], 1.0, 0.0
            )

    def calculate_positions(self):
        """
        Calculate positions based on the signals.

        Returns:
        pd.DataFrame: DataFrame containing the positions for each ticker.
        """
        positions_list = []
        for ticker in self.tickers:
            positions = pd.DataFrame({
                'time': self.data.index,
                'book': self.strategy_name,
                'ticker': ticker,
                'units': np.where(self.data[f'{self.strategy_name}_{ticker}_signal'] == 1.0, 10, -10)
            })
            positions_list.append(positions)
        return pd.concat(positions_list)
```

### Fetch and Format Your Data

Ensure your price data is formatted correctly. The data should be a pandas DataFrame with tickers as columns and a datetime index. Here is an example of how to format your data:

```python
import pandas as pd

# Define tickers and date range
tickers = ['AAPL', 'LMT']
start_date = '2010-01-01'
end_date = '2025-01-01'

# Fetch data (replace this with your data fetching logic)
data = pd.DataFrame({
    'AAPL': np.random.randn(2500) + 100,
    'LMT': np.random.randn(2500) + 200
}, index=pd.date_range(start=start_date, periods=2500))

# Ensure the columns are well named
data.columns = tickers

# Drop rows with missing values
data = data.dropna()

# Convert index to datetime format
data.index = pd.to_datetime(data.index)

# Sort the data by index
data = data.sort_index()
```

### Initialize and Run Backtest

Initialize the backtest with your strategies and run it:

```python
from backtest import Backtest, DisplayBacktest

# Initialize strategies
strategy1 = MovingAverageStrategy(name="StrategyShortMA", data=data, short_window=5, long_window=21)
strategy2 = MovingAverageStrategy(name="StrategyLongMA", data=data, short_window=20, long_window=50)
strategies = [strategy1, strategy2]
weights = {"StrategyShortMA": 0.7, "StrategyLongMA": 0.3}

# Run backtest
backtest = Backtest(data, strategies, weights)
```

### Visualize Results

Use the DisplayBacktest class to visualize the results of your backtest:

```python
# Plot results
display = DisplayBacktest(backtest)
display.plot_book("StrategyShortMA")
display.plot_cumulative_pnl_per_book()
display.plot_cumulative_pnl()
display.plot_individual_pnl()
display.plot_pnl_distribution()
display.plot_signals()  # New method to plot signals if defined at the beginning
```

### Calculate Metrics

Calculate performance metrics for your strategies:

```python
# Get yearly and monthly metrics
yearly_metrics = display.get_metrics(book='StrategyShortMA', resample_period='Y')  # Yearly metrics
monthly_metrics = display.get_metrics(book='StrategyShortMA', resample_period='M')  # Monthly metrics
```

### Export Results

Export the backtest results to an Excel file for further analysis:

```python
# Export excel
backtest.export_excel("backtest_results.xlsx")
```

## Conclusion

The Nara Backtesting Platform provides a powerful and flexible framework for backtesting algorithmic trading strategies. With its comprehensive set of tools, you can define, manage, and evaluate your strategies with ease. Whether you are a seasoned trader or a beginner, this platform offers everything you need to develop and test your trading strategies effectively.

## Upcoming Features and Improvements

We are continuously working to enhance the functionality and usability of the backtesting_package. In the upcoming releases, you can expect the following improvements:

- [implemented in 1.2] Signal Visualization and Export: We plan to introduce features that allow you to visualize trading signals and export them to Excel for further analysis.
- Addition of Options: We will be adding support for options trading, providing more flexibility for your backtesting strategies.
- Enhanced Display Class: The Display class will be improved to offer better visualization and user experience, making it easier to interpret backtesting results.

Stay tuned for these exciting updates!