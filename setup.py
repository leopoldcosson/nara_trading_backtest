from setuptools import setup, find_packages

setup(
    name='backtesting-package',
    version='1.0',
    author='Léopold Cosson',
    author_email='leopoldcosson@gmail.com',
    description='Framework for backtesting algorithmic trading strategies',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/leopoldcosson/backtesting-package',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'tqdm',
        'plotly',
        'numpy',
        'yfinance'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    license='MIT License with Restrictions',
    python_requires='>=3.6',
)
