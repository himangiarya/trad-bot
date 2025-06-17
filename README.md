# Crypto Trading Bot Project

This repository contains a simple example script `crypto_bot.py` that shows how to gather
market data and news from several public sources:

- **Telegram** (via the [Telethon](https://docs.telethon.dev/) client)
- **CoinGecko** prices (via the [pycoingecko](https://github.com/man-c/pycoingecko) library)
- **RSS news feeds** (parsed with `feedparser`)

The script fetches recent messages from a Telegram channel, retrieves token prices
from CoinGecko, reads the latest headlines from an RSS feed and performs a very
basic sentiment check on those headlines.

> **Disclaimer:** This project is for educational purposes only and does not
> provide financial advice. Use any information or analysis produced by the
> script at your own risk.

## Installation

Use `pip` to install the required dependencies:

```bash
pip install pycoingecko telethon feedparser vaderSentiment tweepy
```

## Usage

Set the environment variables required for Telegram access and run the script:

```bash
export TG_API_ID=your_id
export TG_API_HASH=your_hash
export TG_CHANNEL=@example_channel
export TG_ALERT_TARGET=https://t.me/+UdnCRI6yaAkwNGM0
export TOKENS=bitcoin,ethereum
export TWITTER_BEARER_TOKEN=your_twitter_token
export TWITTER_ACCOUNTS=binance,cointelegraph
python crypto_bot.py
```

If `TOKENS` is not set, the bot monitors the default set described below.

If Telegram credentials are not provided, the script will skip reading messages
but will still gather price data and headlines.

The output displays the collected messages, current prices, the latest headlines
and a naive sentiment score for the tokens specified in the script.

### Using CoinGecko

`crypto_bot.py` relies on the [pycoingecko](https://github.com/man-c/pycoingecko)
library to query the CoinGecko API. The `CryptoNewsBot` class includes helper
methods like `fetch_coingecko_prices()` and `fetch_market_overview()` which
demonstrate basic API calls:

```python
from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()
price = cg.get_price(ids="bitcoin", vs_currencies="usd")
market = cg.get_global()
```

These calls provide current prices and global market data such as total market
capitalization and Bitcoin dominance. Network access is required for these
functions to succeed.

### Telegram alert channels

`CryptoNewsBot` can read messages from a list of popular crypto alert and news
channels on Telegram. By default the following channels are monitored:

```
@CryptoWhaleSignals
@BinanceKillers
@UniswapSniper
@FantomDeFi
@SolanaAlpha
@CryptoNekoBot
@CryptoBusy
@CryptoNewsLive
@CoinDeskOfficial
@TokenInsightReport
@Cointelegraph
@WhaleAlertChannel
@Lookonchain
@DeFiAlphaAlerts
@CryptoDiffer
```

Set the `TG_ALERT_CHANNELS` environment variable to a comma-separated list to
override this selection.

### Selecting tokens

By default the bot tracks a handful of widely traded tokens:

```
BNB, CAKE, UNI, BTC, XRP, ETH
```

These correspond to the CoinGecko IDs `binancecoin`, `pancakeswap-token`,
`uniswap`, `bitcoin`, `ripple` and `ethereum`. Set the `TOKENS` environment
variable to a comma-separated list of CoinGecko token IDs if you wish to
monitor a different set.

### Twitter integration

If a `TWITTER_BEARER_TOKEN` is provided, the bot can fetch recent tweets from
accounts listed in `TWITTER_ACCOUNTS` (comma separated). Tweets are included in
the logged output and contribute to the summary message.

### Sending alerts

Set `TG_ALERT_TARGET` to the Telegram chat or channel where summaries should be
sent. It can be a phone number, @username, or invite link. The default is the
public group `https://t.me/+UdnCRI6yaAkwNGM0`. The old `TG_ALERT_PHONE`
variable is still respected for backwards compatibility.

### Continuous monitoring and logs

`crypto_bot.py` runs in an infinite loop, collecting data every five minutes.
Each run is appended to `bot.log` in JSON format so you can review the history
later.


