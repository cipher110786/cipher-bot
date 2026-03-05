import discord
from discord.ext import commands, tasks
import requests
import os
import random

TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API_KEY")

CRYPTO_CHANNEL = int(os.getenv("CRYPTO_CHANNEL", "0"))
CMC_CHANNEL = int(os.getenv("CMC_CHANNEL", "0"))
NEWS_CHANNEL = int(os.getenv("NEWS_CHANNEL", "0"))
WHALE_CHANNEL = int(os.getenv("WHALE_CHANNEL", "0"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    crypto_updates.start()
    cmc_updates.start()
    news_updates.start()
    whale_updates.start()

# =================================
# BITCOIN MARKET INTELLIGENCE
# =================================

@tasks.loop(minutes=30)
async def crypto_updates():

    channel = bot.get_channel(CRYPTO_CHANNEL)

    try:

        url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        r = requests.get(url).json()

        price = float(r["lastPrice"])
        change = float(r["priceChangePercent"])
        volume = float(r["volume"])

        sentiment = "Bullish 📈" if change > 0 else "Bearish 📉"

        msg = f"""
🚨 **Bitcoin Market Intelligence**

💰 Price: ${price:,.2f}
📊 24h Change: {change:.2f}%
📦 Volume: {volume:,.0f}

🧠 Market Sentiment: **{sentiment}**

#crypto #bitcoin
"""

        await channel.send(msg)

    except Exception as e:
        print("Crypto Error:", e)

# =================================
# TOP COINS FROM CMC
# =================================

@tasks.loop(minutes=30)
async def cmc_updates():

    channel = bot.get_channel(CMC_CHANNEL)

    try:

        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

        headers = {
            "X-CMC_PRO_API_KEY": CMC_API
        }

        params = {
            "start": "1",
            "limit": "10",
            "convert": "USD"
        }

        r = requests.get(url, headers=headers, params=params).json()

        coins = r["data"]

        msg = "📊 **Top 10 Cryptocurrencies**\n\n"

        for c in coins[:10]:

            name = c["name"]
            price = c["quote"]["USD"]["price"]
            change = c["quote"]["USD"]["percent_change_24h"]

            emoji = "🟢" if change > 0 else "🔴"

            msg += f"{emoji} {name} — ${price:,.2f} ({change:.2f}%)\n"

        await channel.send(msg)

    except Exception as e:
        print("CMC Error:", e)

# =================================
# CRYPTO NEWS + FEAR GREED
# =================================

@tasks.loop(minutes=30)
async def news_updates():

    channel = bot.get_channel(NEWS_CHANNEL)

    try:

        news_url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        news = requests.get(news_url).json()

        article = news["Data"][0]

        title = article["title"]
        link = article["url"]

        fear_url = "https://api.alternative.me/fng/"
        fear = requests.get(fear_url).json()

        index = fear["data"][0]["value"]
        sentiment = fear["data"][0]["value_classification"]

        msg = f"""
📰 **Crypto News**

{title}

🔗 {link}

😱 **Fear & Greed Index**

Value: {index}
Sentiment: **{sentiment}**
"""

        await channel.send(msg)

    except Exception as e:
        print("News Error:", e)

# =================================
# WHALE ALERTS
# =================================

@tasks.loop(minutes=30)
async def whale_updates():

    channel = bot.get_channel(WHALE_CHANNEL)

    try:

        url = "https://api.whale-alert.io/v1/transactions?api_key=demo&min_value=10000000"
        r = requests.get(url).json()

        if "transactions" in r:

            tx = r["transactions"][0]

            amount = tx["amount"]
            symbol = tx["symbol"]
            usd = tx["amount_usd"]
            blockchain = tx["blockchain"]

            msg = f"""
🐋 **Whale Transfer Detected**

{amount} {symbol}

💰 Value: ${usd:,.0f}
⛓ Blockchain: {blockchain}
"""

            await channel.send(msg)

    except Exception as e:
        print("Whale Error:", e)

bot.run(TOKEN)
