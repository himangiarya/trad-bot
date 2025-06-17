import os
import asyncio
import json
from typing import List, Dict

from pycoingecko import CoinGeckoAPI
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import tweepy

DEFAULT_TOKENS = [
    "binancecoin",      # BNB
    "pancakeswap-token",  # CAKE
    "uniswap",          # UNI
    "bitcoin",          # BTC
    "ripple",           # XRP
    "ethereum",         # ETH
]

DEFAULT_ALERT_CHANNELS = [
    "@CryptoWhaleSignals",
    "@BinanceKillers",
    "@UniswapSniper",
    "@FantomDeFi",
    "@SolanaAlpha",
    "@CryptoNekoBot",
    "@CryptoBusy",
    "@CryptoNewsLive",
    "@CoinDeskOfficial",
    "@TokenInsightReport",
    "@Cointelegraph",
    "@WhaleAlertChannel",
    "@Lookonchain",
    "@DeFiAlphaAlerts",
    "@CryptoDiffer",
]

# default Telegram destination for alerts (a public group link)
DEFAULT_ALERT_TARGET = "https://t.me/+UdnCRI6yaAkwNGM0"

LOG_FILE = "bot.log"

try:
    from telethon import TelegramClient
except ImportError:  # optional dependency
    TelegramClient = None


class CryptoNewsBot:
    """Gather basic market data from Telegram, CoinGecko and RSS feeds."""

    def __init__(self,
                 tg_api_id: str | None = None,
                 tg_api_hash: str | None = None,
                 tg_channel: str | None = None,
                 tg_alert_channels: List[str] | None = None,
                 alert_target: str | None = None,
                 twitter_bearer: str | None = None,
                 twitter_accounts: List[str] | None = None):
        self.tg_api_id = tg_api_id or os.getenv("TG_API_ID")
        self.tg_api_hash = tg_api_hash or os.getenv("TG_API_HASH")
        self.tg_channel = tg_channel or os.getenv("TG_CHANNEL")

        alert_env = os.getenv("TG_ALERT_CHANNELS")
        if tg_alert_channels:
            self.tg_alert_channels = tg_alert_channels
        elif alert_env:
            self.tg_alert_channels = [c.strip() for c in alert_env.split(',') if c.strip()]
        else:
            self.tg_alert_channels = DEFAULT_ALERT_CHANNELS

        target_env = os.getenv("TG_ALERT_TARGET") or os.getenv("TG_ALERT_PHONE")
        if alert_target:
            self.alert_target = alert_target
        elif target_env:
            self.alert_target = target_env
        else:
            self.alert_target = DEFAULT_ALERT_TARGET

        self.twitter_bearer = twitter_bearer or os.getenv("TWITTER_BEARER_TOKEN")
        accounts_env = os.getenv("TWITTER_ACCOUNTS")
        if twitter_accounts:
            self.twitter_accounts = twitter_accounts
        elif accounts_env:
            self.twitter_accounts = [a.strip() for a in accounts_env.split(',') if a.strip()]
        else:
            self.twitter_accounts = []

        self.cg = CoinGeckoAPI()
        self.analyzer = SentimentIntensityAnalyzer()
        if self.twitter_bearer:
            self.twitter_client = tweepy.Client(self.twitter_bearer)
        else:
            self.twitter_client = None
        if self.tg_api_id and self.tg_api_hash and TelegramClient:
            self.client = TelegramClient('session', self.tg_api_id, self.tg_api_hash)
        else:
            self.client = None

    async def fetch_telegram_messages(self, limit: int = 10) -> List[str]:
        """Fetch the latest messages from the configured Telegram channel."""
        if not self.client or not self.tg_channel:
            return []
        await self.client.start()
        msgs = []
        async for msg in self.client.iter_messages(self.tg_channel, limit=limit):
            if msg.text:
                msgs.append(msg.text)
        await self.client.disconnect()
        return msgs

    async def fetch_alerts(self, limit: int = 5) -> Dict[str, List[str]]:
        """Fetch messages from the configured alert channels."""
        if not self.client:
            return {}
        await self.client.start()
        results: Dict[str, List[str]] = {}
        for chan in self.tg_alert_channels:
            msgs: List[str] = []
            async for msg in self.client.iter_messages(chan, limit=limit):
                if msg.text:
                    msgs.append(msg.text)
            results[chan] = msgs
        await self.client.disconnect()
        return results

    def parse_alert_actions(self, alerts: Dict[str, List[str]]) -> List[str]:
        """Look for whale or listing keywords and suggest reactions."""
        actions: List[str] = []
        buy_keywords = ["listing", "whale buy", "new pair"]
        sell_keywords = ["whale sell", "rug", "exit"]
        for channel, msgs in alerts.items():
            for msg in msgs:
                lowered = msg.lower()
                if any(k in lowered for k in buy_keywords):
                    actions.append(f"BUY signal from {channel}: {msg}")
                if any(k in lowered for k in sell_keywords):
                    actions.append(f"SELL signal from {channel}: {msg}")
        return actions

    def fetch_tweets(self, limit: int = 5) -> Dict[str, List[str]]:
        """Retrieve recent tweets from the configured accounts."""
        if not self.twitter_client or not self.twitter_accounts:
            return {}
        results: Dict[str, List[str]] = {}
        for account in self.twitter_accounts:
            try:
                tweets = self.twitter_client.search_recent_tweets(
                    query=f"from:{account}", max_results=limit
                ).data or []
                results[account] = [t.text for t in tweets]
            except Exception:
                results[account] = []
        return results

    async def send_alert(self, text: str) -> None:
        """Send a message to the configured chat or phone."""
        if not self.client:
            return
        await self.client.start()
        await self.client.send_message(self.alert_target, text)
        await self.client.disconnect()

    def log_result(self, result: Dict) -> None:
        with open(LOG_FILE, "a") as fh:
            fh.write(json.dumps(result) + "\n")

    def fetch_coingecko_prices(self, tokens: List[str]) -> Dict[str, float | None]:
        """Get USD prices for a list of tokens via CoinGecko API."""
        prices = {}
        for token in tokens:
            try:
                data = self.cg.get_price(ids=token, vs_currencies='usd')
                prices[token] = data.get(token, {}).get('usd')
            except Exception:
                prices[token] = None
        return prices

    def fetch_market_overview(self) -> Dict[str, float | None]:
        """Retrieve a few global market metrics from CoinGecko."""
        try:
            data = self.cg.get_global().get('data', {})
            return {
                'market_cap_usd': data.get('total_market_cap', {}).get('usd'),
                'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd'),
                'btc_dominance': data.get('market_cap_percentage', {}).get('btc'),
            }
        except Exception:
            return {}

    def fetch_news(self, feed_url: str = "https://feeds.feedburner.com/CoinDesk") -> List[str]:
        """Retrieve headlines from an RSS feed."""
        feed = feedparser.parse(feed_url)
        return [entry.title for entry in feed.entries[:10]]

    def analyze_sentiment(self, tokens: List[str], headlines: List[str]) -> Dict[str, str]:
        """Use VADER sentiment scores to determine Buy/Sell/Hold."""
        results: Dict[str, str] = {}
        for token in tokens:
            scores = []
            token_name = token.replace('-', ' ')
            for title in headlines:
                if token_name in title.lower():
                    scores.append(self.analyzer.polarity_scores(title)['compound'])
            if scores:
                avg = sum(scores) / len(scores)
            else:
                avg = 0.0
            if avg > 0.2:
                results[token] = 'Buy'
            elif avg < -0.2:
                results[token] = 'Sell'
            else:
                results[token] = 'Hold'
        return results

    async def run_once(self, tokens: List[str]):
        telegram_msgs = await self.fetch_telegram_messages(5)
        alert_msgs = await self.fetch_alerts(3)
        tweets = self.fetch_tweets(3)
        prices = self.fetch_coingecko_prices(tokens)
        market = self.fetch_market_overview()
        news = self.fetch_news()
        sentiment = self.analyze_sentiment(tokens, news)
        actions = self.parse_alert_actions(alert_msgs)
        result = {
            "telegram": telegram_msgs,
            "alerts": alert_msgs,
            "tweets": tweets,
            "prices": prices,
            "market": market,
            "news": news,
            "sentiment": sentiment,
            "actions": actions,
        }
        self.log_result(result)
        return result


async def main() -> None:
    bot = CryptoNewsBot()
    print("This example does not provide financial advice.")
    tokens_env = os.getenv("TOKENS")
    if tokens_env:
        tokens = [t.strip() for t in tokens_env.split(',') if t.strip()]
    else:
        tokens = DEFAULT_TOKENS
    while True:
        result = await bot.run_once(tokens)
        summary = f"Prices: {result['prices']}\nSentiment: {result['sentiment']}\nActions: {', '.join(result['actions']) if result['actions'] else 'none'}"
        await bot.send_alert(summary)
        print(summary)
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
