# setup.py
from setuptools import setup, find_packages

setup(
    name='backtesting_package',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'plotly',
        'statsmodels',
        'tqdm',
        'yfinance'
    ],
    entry_points={
        'console_scripts': [
            'backtest=main:main',
        ],
    },
)