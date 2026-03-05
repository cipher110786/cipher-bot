import discord
from discord.ext import commands, tasks
import aiohttp
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API_KEY")
BINANCE_KEY = os.getenv("BINANCE_API_KEY")

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------------
# FETCH CRYPTO DATA (BINANCE)
# -----------------------------
async def get_crypto():
    url = "https://api.binance.com/api/v3/ticker/price"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    btc = next(x for x in data if x["symbol"] == "BTCUSDT")
    eth = next(x for x in data if x["symbol"] == "ETHUSDT")

    return f"""
🚀 **Crypto Update**

BTC: ${btc['price']}
ETH: ${eth['price']}
"""


# -----------------------------
# FETCH COINMARKETCAP
# -----------------------------
async def get_cmc():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers = {
        "X-CMC_PRO_API_KEY": CMC_API
    }

    params = {
        "symbol": "BTC,ETH"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            data = await resp.json()

    btc = data["data"]["BTC"]["quote"]["USD"]["price"]
    eth = data["data"]["ETH"]["quote"]["USD"]["price"]

    return f"""
📊 **CoinMarketCap**

BTC: ${btc:,.2f}
ETH: ${eth:,.2f}
"""


# -----------------------------
# WHALE ALERT
# -----------------------------
async def get_whale():
    url = "https://api.whale-alert.io/v1/transactions?min_value=5000000"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if "transactions" not in data:
        return "🐋 No whale activity detected."

    tx = data["transactions"][0]

    return f"""
🐋 **Whale Alert**

{tx['amount']} {tx['symbol']}
From: {tx['from']['owner']}
To: {tx['to']['owner']}
"""


# -----------------------------
# PSX DATA
# -----------------------------
async def get_psx():
    url = "https://dps.psx.com.pk/indices/KSE100"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    index = data["data"]["value"]

    return f"""
🇵🇰 **PSX Update**

KSE-100 Index: {index}
"""


# -----------------------------
# LOOP EVERY 30 MINUTES
# -----------------------------
@tasks.loop(minutes=30)
async def market_updates():

    channel = bot.get_channel(CHANNEL_ID)

    try:
        crypto = await get_crypto()
        cmc = await get_cmc()
        whale = await get_whale()
        psx = await get_psx()

        await channel.send(crypto)
        await channel.send(cmc)
        await channel.send(whale)
        await channel.send(psx)

    except Exception as e:
        print("Update error:", e)


# -----------------------------
# BOT READY
# -----------------------------
@bot.event
async def on_ready():
    print(f"BOT CONNECTED: {bot.user}")
    market_updates.start()


bot.run(TOKEN)
