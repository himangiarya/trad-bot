# Crypto Telegram Bot

This project contains a simple Telegram bot that sends cryptocurrency price alerts and news updates. It uses scheduled tasks to periodically fetch data and can generate basic buy/sell/hold advice using the OpenAI API.

## Features

- Sends price updates for configured tokens every 30 minutes.
- Provides AI-generated buy/sell/hold analysis based on recent price data.
- Sends news related to each token every hour.
- Sends general cryptocurrency news every 2 hours.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file with the following variables:
   ```bash
   TELEGRAM_TOKEN=your-telegram-bot-token
   CHAT_ID=your-chat-id
   PRICE_API_URL=https://your-price-api.com
   NEWS_API_URL=https://your-news-api.com/v2/everything
   NEWS_API_TOKEN=your-news-api-token
   OPENAI_API_KEY=your-openai-key
   TOKENS=bitcoin,ethereum
   ```
3. Run the bot locally:
   ```bash
   python -m src.bot
   ```

## Deploying to Render

1. Push the repository to GitHub.
2. Create a new Web Service on Render and connect it to your repository.
3. Set the environment variables from your `.env` file in the Render dashboard.
4. Render will use the `Procfile` to start the bot.

## Notes

- The bot relies on external APIs for price data and news. You may need to sign up for API keys depending on the provider.
- The AI analysis feature requires an OpenAI API key. If not provided, the bot will skip analysis.
