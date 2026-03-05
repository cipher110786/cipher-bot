import discord
import requests
import asyncio
from bs4 import BeautifulSoup
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# CHANNEL IDs
PSX_CHANNEL = 1478816955971665990
NEWS_CHANNEL = 1478816955971665990
CRYPTO_CHANNEL = 1478816867828240626
GLOBAL_CHANNEL = 1478817069415010425
COMMODITY_CHANNEL = 1478816867828240626
WHALE_CHANNEL = 1478816921649545256

ROLE_ID = 1478715069453041676


# ---------------- PSX INDEX ---------------- #

async def psx_index():

    await client.wait_until_ready()
    channel = client.get_channel(PSX_CHANNEL)

    while not client.is_closed():

        try:

            url = "https://dps.psx.com.pk/indices/KSE100"
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
            data = r.json()

            value = data["data"]["value"]
            change = data["data"]["change"]
            percent = data["data"]["percent_change"]

            msg = f"""
📊 **PSX MARKET UPDATE**

KSE-100 Index: **{value}**
Change: **{change} ({percent}%)**

<@&{ROLE_ID}>
"""

            await channel.send(msg)

        except Exception as e:
            print("PSX Error:", e)

        await asyncio.sleep(3600)


# ---------------- PSX NEWS ---------------- #

async def psx_news():

    await client.wait_until_ready()
    channel = client.get_channel(NEWS_CHANNEL)

    while not client.is_closed():

        try:

            url = "https://dps.psx.com.pk/news"
            r = requests.get(url)
            soup = BeautifulSoup(r.text,"html.parser")

            headlines = soup.find_all("h3")[:5]

            news = "\n".join([f"• {h.text}" for h in headlines])

            msg = f"""
📰 **PSX MARKET NEWS**

{news}

<@&{ROLE_ID}>
"""

            await channel.send(msg)

        except Exception as e:
            print("News Error:", e)

        await asyncio.sleep(7200)


# ---------------- CRYPTO ---------------- #

async def crypto_update():

    await client.wait_until_ready()
    channel = client.get_channel(CRYPTO_CHANNEL)

    while not client.is_closed():

        try:

            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple&vs_currencies=usd"

            data = requests.get(url).json()

            btc = data["bitcoin"]["usd"]
            eth = data["ethereum"]["usd"]
            sol = data["solana"]["usd"]
            xrp = data["ripple"]["usd"]

            msg = f"""
🪙 **CRYPTO MARKET**

BTC : ${btc}
ETH : ${eth}
SOL : ${sol}
XRP : ${xrp}

<@&{ROLE_ID}>
"""

            await channel.send(msg)

        except Exception as e:
            print("Crypto Error:",e)

        await asyncio.sleep(1800)


# ---------------- COMMODITIES ---------------- #

async def commodities():

    await client.wait_until_ready()
    channel = client.get_channel(COMMODITY_CHANNEL)

    while not client.is_closed():

        try:

            gold = requests.get("https://api.coinbase.com/v2/prices/XAU-USD/spot").json()
            gold_price = gold["data"]["amount"]

            msg = f"""
🛢 **COMMODITIES**

Gold : ${gold_price}

<@&{ROLE_ID}>
"""

            await channel.send(msg)

        except Exception as e:
            print("Commodity Error:",e)

        await asyncio.sleep(3600)


# ---------------- GLOBAL MARKETS ---------------- #

async def global_market():

    await client.wait_until_ready()
    channel = client.get_channel(GLOBAL_CHANNEL)

    while not client.is_closed():

        try:

            url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EGSPC,%5EIXIC,%5EDJI"
            r = requests.get(url)
            data = r.json()

            sp = data["quoteResponse"]["result"][0]["regularMarketPrice"]
            nasdaq = data["quoteResponse"]["result"][1]["regularMarketPrice"]
            dow = data["quoteResponse"]["result"][2]["regularMarketPrice"]

            msg = f"""
🌍 **GLOBAL MARKETS**

S&P 500 : {sp}
NASDAQ : {nasdaq}
DOW : {dow}

<@&{ROLE_ID}>
"""

            await channel.send(msg)

        except Exception as e:
            print("Global Error:",e)

        await asyncio.sleep(3600)


# ---------------- WHALE ALERT ---------------- #

async def whale_alert():

    await client.wait_until_ready()
    channel = client.get_channel(WHALE_CHANNEL)

    while not client.is_closed():

        try:

            url = "https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=50"

            trades = requests.get(url).json()

            for t in trades:

                value = float(t["price"]) * float(t["qty"])

                if value > 500000:

                    msg = f"""
🐋 **WHALE ALERT**

Large BTC trade detected
Value : ${value:,.0f}

<@&{ROLE_ID}>
"""

                    await channel.send(msg)

        except Exception as e:
            print("Whale Error:",e)

        await asyncio.sleep(300)


# ---------------- BOT READY ---------------- #

@client.event
async def on_ready():

    print("Bot Online")

    client.loop.create_task(psx_index())
    client.loop.create_task(psx_news())
    client.loop.create_task(crypto_update())
    client.loop.create_task(global_market())
    client.loop.create_task(commodities())
    client.loop.create_task(whale_alert())


client.run(TOKEN)
