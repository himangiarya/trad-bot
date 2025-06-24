import logging
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


def load_env():
    from dotenv import load_dotenv
    load_dotenv()


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PRICE_API_URL = os.getenv("PRICE_API_URL")  # e.g. https://api.coincap.io/v2/assets
NEWS_API_URL = os.getenv("NEWS_API_URL")  # e.g. https://newsapi.org/v2/everything
NEWS_API_TOKEN = os.getenv("NEWS_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOKENS = os.getenv("TOKENS", "bitcoin,ethereum").split(",")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Crypto bot started. You will receive updates periodically.")


def fetch_price(token: str) -> float:
    if not PRICE_API_URL:
        logger.warning("PRICE_API_URL not set")
        return 0.0
    try:
        response = requests.get(f"{PRICE_API_URL}/{token}")
        response.raise_for_status()
        data = response.json()
        return float(data.get("data", {}).get("priceUsd", 0))
    except Exception as exc:
        logger.error("Failed to fetch price for %s: %s", token, exc)
        return 0.0


def fetch_token_news(token: str) -> str:
    if not NEWS_API_URL or not NEWS_API_TOKEN:
        logger.warning("NEWS_API_URL or NEWS_API_TOKEN not set")
        return ""
    try:
        params = {
            "q": token,
            "apiKey": NEWS_API_TOKEN,
            "pageSize": 3,
            "sortBy": "publishedAt",
        }
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        headlines = [article["title"] for article in articles]
        return "\n".join(headlines)
    except Exception as exc:
        logger.error("Failed to fetch news: %s", exc)
        return ""


def ai_analysis(prices: list[float]) -> str:
    if not OPENAI_API_KEY:
        return "AI analysis not configured."
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        prompt = (
            "Given the recent prices: "
            + ", ".join(map(str, prices))
            + ". Should I buy, sell, or hold?"
        )
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("OpenAI request failed: %s", exc)
        return "AI analysis unavailable."


def price_job(app, chat_id: int, token: str):
    price = fetch_price(token)
    if price:
        message = f"Current price of {token}: ${price:.2f}"
    else:
        message = f"Could not fetch price for {token}."
    logger.info(message)
    app.bot.send_message(chat_id=chat_id, text=message)

    # Dummy price list for AI analysis; in real usage gather historical prices
    analysis = ai_analysis([price])
    if analysis:
        app.bot.send_message(chat_id=chat_id, text=analysis)


def token_news_job(app, chat_id: int, token: str):
    news = fetch_token_news(token)
    if news:
        app.bot.send_message(chat_id=chat_id, text=f"News for {token}:\n{news}")


def general_news_job(app, chat_id: int):
    news = fetch_token_news("crypto")
    if news:
        app.bot.send_message(chat_id=chat_id, text=f"General crypto news:\n{news}")


def main() -> None:
    load_env()
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN environment variable missing")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    chat_id = int(os.getenv("CHAT_ID", "0"))
    scheduler = BackgroundScheduler()
    for token in TOKENS:
        scheduler.add_job(
            price_job,
            "interval",
            minutes=30,
            args=[app, chat_id, token],
            id=f"price_{token}",
            replace_existing=True,
        )
        scheduler.add_job(
            token_news_job,
            "interval",
            hours=1,
            args=[app, chat_id, token],
            id=f"news_{token}",
            replace_existing=True,
        )
    scheduler.add_job(
        general_news_job,
        "interval",
        hours=2,
        args=[app, chat_id],
        id="general_news",
        replace_existing=True,
    )
    scheduler.start()

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
