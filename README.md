# crypto-futures-trading-bot

This is a Python-based crypto trading bot that performs technical analysis using TA-Lib and provides trading signals based on the Alligator indicator. The bot fetches trading pairs from APIs, fetches candlestick data, and manages trading positions.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Code Explanation](#code-explanation)

## Installation

1. Clone this repository to your local machine:

```bash
git clone https://github.com/shishohf/crypto-futures-trading-bot.git
cd crypto-futures-trading-bot
```

2. Install the required Python packages using the following command:

```bash
pip install -r requirements.txt
```

3. Configure the `config.json` file in the root directory with your bot's configuration, API keys, and other settings.

4. Run the trading bot:

```bash
python bot.py
```

##How It Works

- The bot uses the TA-Lib library to perform technical analysis on trading data pulled from Binance on symbols available on BingX and generates automated trading signals.

- The Crypto cog fetches trading pairs and candlestick data from the APIs using asynchronous requests.

- The bot's position manager loops through the fetched pair and handles everything. Soon it'll open the trades and monitor them.

##Code Explanation

    utils/ta.py contains functions for performing technical analysis.

    utils/api.py includes functions for fetching trading pairs and candlestick data from APIs.

    crypto.py defines the Crypto cog, which manages the entire trading functionality of the bot.

    bot.py is the entry point for running the trading bot.
