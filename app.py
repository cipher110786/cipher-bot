import discord
from discord.ext import commands, tasks
import requests
import os

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


# ==========================
# CRYPTO MARKET UPDATE
# ==========================

@tasks.loop(minutes=30)
async def crypto_updates():

    channel = bot.get_channel(CRYPTO_CHANNEL)

    try:
        url = "https://api.coincap.io/v2/assets/bitcoin"
        data = requests.get(url).json()

        price = float(data["data"]["priceUsd"])
        change = float(data["data"]["changePercent24Hr"])

        msg = f"""
🚨 **Bitcoin Market Update**

💰 Price: ${price:,.2f}
📉 24h Change: {change:.2f}%

#crypto #bitcoin
"""

        await channel.send(msg)

    except Exception as e:
        print("Crypto Error:", e)


# ==========================
# CMC TOP COINS
# ==========================

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
            "limit": "5",
            "convert": "USD"
        }

        r = requests.get(url, headers=headers, params=params).json()

        coins = r["data"]

        msg = "📊 **Top 5 Cryptocurrencies**\n\n"

        for c in coins:

            name = c["name"]
            price = c["quote"]["USD"]["price"]
            change = c["quote"]["USD"]["percent_change_24h"]

            msg += f"{name} — ${price:,.2f} ({change:.2f}%)\n"

        await channel.send(msg)

    except Exception as e:
        print("CMC Error:", e)


# ==========================
# CRYPTO NEWS
# ==========================

@tasks.loop(minutes=30)
async def news_updates():

    channel = bot.get_channel(NEWS_CHANNEL)

    try:

        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"

        r = requests.get(url).json()

        article = r["Data"][0]

        title = article["title"]
        link = article["url"]

        msg = f"""
📰 **Crypto News**

{title}

🔗 {link}
"""

        await channel.send(msg)

    except Exception as e:
        print("News Error:", e)


# ==========================
# WHALE ALERT
# ==========================

@tasks.loop(minutes=30)
async def whale_updates():

    channel = bot.get_channel(WHALE_CHANNEL)

    try:

        url = "https://api.whale-alert.io/v1/transactions?api_key=demo&min_value=5000000"

        r = requests.get(url).json()

        if "transactions" in r:

            tx = r["transactions"][0]

            amount = tx["amount"]
            symbol = tx["symbol"]
            usd = tx["amount_usd"]

            msg = f"""
🐋 **Whale Alert**

{amount} {symbol} moved

💰 Value: ${usd:,.0f}
"""

            await channel.send(msg)

    except Exception as e:
        print("Whale Error:", e)


bot.run(TOKEN)
