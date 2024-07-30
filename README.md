
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
    def __init__(self, name, data, short_window, long_window):
        super().__init__(name, data)
        self.short_window = short_window
        self.long_window = long_window
        self.tickers = data.columns

        # Compute moving averages for each ticker
        for ticker in self.tickers:
            self.data[f'{self.strategy_name}_{ticker}_short_ma'] = self.data[ticker].rolling(window=self.short_window).mean()
            self.data[f'{self.strategy_name}_{ticker}_long_ma'] = self.data[ticker].rolling(window=self.long_window).mean()

    def calculate_signal(self):
        for ticker in self.tickers:
            self.data[f'{self.strategy_name}_{ticker}_signal'] = 0.0
            self.data[f'{self.strategy_name}_{ticker}_signal'][self.short_window:] = np.where(
                self.data[f'{self.strategy_name}_{ticker}_short_ma'][self.short_window:] > self.data[f'{self.strategy_name}_{ticker}_long_ma'][self.short_window:], 1.0, 0.0
            )

    def calculate_positions(self):
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

## Examples

### Example 1: Simple Moving Average Strategy

Define a simple moving average strategy and run a backtest:

```python
from backtest import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, name, data, short_window, long_window):
        super().__init__(name, data)
        self.short_window = short_window
        self.long_window = long_window
        self.tickers = data.columns

        # Compute moving averages for each ticker
        for ticker in self.tickers:
            self.data[f'{self.strategy_name}_{ticker}_short_ma'] = self.data[ticker].rolling(window=self.short_window).mean()
            self.data[f'{self.strategy_name}_{ticker}_long_ma'] = self.data[ticker].rolling window=self.long_window).mean()

    def calculate_signal(self):
        for ticker in self.tickers:
            self.data[f'{self.strategy_name}_{ticker}_signal'] = 0.0
            self.data[f'{self.strategy_name}_{ticker}_signal'][self.short_window:] = np.where(
                self.data[f'{self.strategy_name}_{ticker}_short_ma'][self.short_window:] > self.data[f'{self.strategy_name}_{ticker}_long_ma'][self.short_window:], 1.0, 0.0
            )

    def calculate_positions(self):
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

### Example 2: Multiple Strategies with Different Weights

Run a backtest with multiple strategies and different weights:

```python
from backtest import Backtest, DisplayBacktest

# Initialize strategies
strategy1 = MovingAverageStrategy(name="StrategyShortMA", data=data, short_window=5, long_window=21)
strategy2 = MovingAverageStrategy(name="StrategyLongMA", data=data, short_window=20, long_window=50)
strategies = [strategy1, strategy2]
weights = {"StrategyShortMA": 0.7, "StrategyLongMA": 0.3}

# Run backtest
backtest = Backtest(data, strategies, weights)

# Plot results
display = DisplayBacktest(backtest)
display.plot_book("StrategyShortMA")
display.plot_cumulative_pnl_per_book()
display.plot_cumulative_pnl()
display.plot_individual_pnl()
display.plot_pnl_distribution()

# Get yearly and monthly metrics
yearly_metrics = display.get_metrics(book='StrategyShortMA', resample_period='Y')  # Yearly metrics
monthly_metrics = display.get_metrics(book='StrategyShortMA', resample_period='M')  # Monthly metrics

# Export excel
backtest.export_excel("backtest_results.xlsx")
```

## Conclusion

The Nara Backtesting Platform provides a powerful and flexible framework for backtesting algorithmic trading strategies. With its comprehensive set of tools, you can define, manage, and evaluate your strategies with ease. Whether you are a seasoned trader or a beginner, this platform offers everything you need to develop and test your trading strategies effectively.
