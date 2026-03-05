import discord
import os
import requests
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

CRYPTO_CHANNEL = int(os.getenv("CRYPTO_CHANNEL"))
CMC_CHANNEL = int(os.getenv("CMC_CHANNEL"))
NEWS_CHANNEL = int(os.getenv("NEWS_CHANNEL"))
WHALE_CHANNEL = int(os.getenv("WHALE_CHANNEL"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# -------- DATA FUNCTIONS -------- #

def get_crypto():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        price = r.json()["price"]
        return f"BTC Price: ${price}"
    except:
        return "Crypto data unavailable"

def get_cmc():
    try:
        r = requests.get("https://api.coincap.io/v2/assets/bitcoin")
        price = r.json()["data"]["priceUsd"]
        return f"CMC BTC Price: ${round(float(price),2)}"
    except:
        return "CMC data unavailable"

def get_news():
    return "📰 Market Update: Monitor BTC volatility and macro news."

def get_whale():
    return "🐋 Whale Alert: Large BTC movement detected on blockchain."

# -------- LOOP -------- #

async def update_loop():
    await client.wait_until_ready()

    while not client.is_closed():

        crypto_channel = client.get_channel(CRYPTO_CHANNEL)
        cmc_channel = client.get_channel(CMC_CHANNEL)
        news_channel = client.get_channel(NEWS_CHANNEL)
        whale_channel = client.get_channel(WHALE_CHANNEL)

        if crypto_channel:
            await crypto_channel.send(get_crypto())

        if cmc_channel:
            await cmc_channel.send(get_cmc())

        if news_channel:
            await news_channel.send(get_news())

        if whale_channel:
            await whale_channel.send(get_whale())

        print("Updates sent")

        await asyncio.sleep(1800)  # 30 minutes

# -------- BOT READY -------- #

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(update_loop())

client.run(TOKEN)
