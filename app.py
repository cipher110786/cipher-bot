import discord
import aiohttp
import asyncio
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TOKEN")
CMC_API = os.getenv("CMC_API_KEY")
BINANCE_API = os.getenv("BINANCE_API_KEY")

ROLE_ID = 1478820285263122572

CHANNELS = {
    "psx":1478816955971665990,
    "crypto":1478816867828240626,
    "global":1478817069415010425,
    "commodities":1478816867828240626,
    "whale":1478816921649545256
}

HEADERS = {"User-Agent":"Mozilla/5.0"}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ---------------- CRYPTO ---------------- #

async def crypto_monitor():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["crypto"])

    url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers={
        "X-CMC_PRO_API_KEY":CMC_API
    }

    params={
        "symbol":"BTC,ETH,SOL,BNB,XRP"
    }

    while not client.is_closed():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url,headers=headers,params=params) as r:
                    data=await r.json()

                    btc=data["data"]["BTC"]["quote"]["USD"]["price"]
                    eth=data["data"]["ETH"]["quote"]["USD"]["price"]
                    sol=data["data"]["SOL"]["quote"]["USD"]["price"]

                    msg=f"""
🪙 **CRYPTO MARKET**

₿ BTC : ${btc:,.0f}
Ξ ETH : ${eth:,.0f}
◎ SOL : ${sol:,.0f}

<@&{ROLE_ID}>
"""
                    await channel.send(msg)

        except Exception as e:
            print("CMC Error:",e)

        await asyncio.sleep(900)


# ---------------- GLOBAL MARKETS ---------------- #

async def global_monitor():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["global"])

    while not client.is_closed():
        try:

            async with aiohttp.ClientSession() as session:

                url="https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EGSPC,%5EDJI,%5EIXIC"

                async with session.get(url,headers=HEADERS) as r:
                    text=await r.text()

                    if "quoteResponse" not in text:
                        print("Yahoo blocked request")
                    else:
                        data=await r.json()

                        sp=data["quoteResponse"]["result"][0]["regularMarketPrice"]
                        dj=data["quoteResponse"]["result"][1]["regularMarketPrice"]
                        nq=data["quoteResponse"]["result"][2]["regularMarketPrice"]

                        msg=f"""
🌍 **GLOBAL MARKETS**

S&P500 : {sp}
Dow Jones : {dj}
Nasdaq : {nq}

<@&{ROLE_ID}>
"""
                        await channel.send(msg)

        except Exception as e:
            print("Global Error:",e)

        await asyncio.sleep(1800)


# ---------------- COMMODITIES ---------------- #

async def commodity_monitor():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["commodities"])

    while not client.is_closed():
        try:

            async with aiohttp.ClientSession() as session:

                url="https://api.coincap.io/v2/assets"

                async with session.get(url) as r:
                    data=await r.json()

                    gold=next(x for x in data["data"] if x["symbol"]=="XAU")
                    silver=next(x for x in data["data"] if x["symbol"]=="XAG")

                    msg=f"""
🛢 **COMMODITIES**

🥇 Gold : ${float(gold['priceUsd']):,.0f}
🥈 Silver : ${float(silver['priceUsd']):,.2f}

<@&{ROLE_ID}>
"""

                    await channel.send(msg)

        except Exception as e:
            print("Commodity Error:",e)

        await asyncio.sleep(3600)


# ---------------- PSX ---------------- #

async def psx_monitor():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["psx"])

    while not client.is_closed():
        try:

            async with aiohttp.ClientSession() as session:

                url="https://dps.psx.com.pk/"

                async with session.get(url,headers=HEADERS) as r:

                    html=await r.text()
                    soup=BeautifulSoup(html,"html.parser")

                    index=soup.find("span",class_="index-value")

                    if index:
                        value=index.text.strip()

                        msg=f"""
🇵🇰 **PSX MARKET**

KSE-100 Index : {value}

<@&{ROLE_ID}>
"""
                        await channel.send(msg)
                    else:
                        print("PSX structure changed")

        except Exception as e:
            print("PSX Error:",e)

        await asyncio.sleep(3600)


# ---------------- WHALE TRACKER ---------------- #

async def whale_tracker():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["whale"])

    while not client.is_closed():

        try:

            async with aiohttp.ClientSession() as session:

                url="https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=20"

                async with session.get(url) as r:

                    data=await r.json()

                    for t in data:

                        usd=float(t["price"])*float(t["qty"])

                        if usd>1000000:

                            msg=f"""
🐋 **WHALE ALERT**

Large BTC trade detected
Value : ${usd:,.0f}

<@&{ROLE_ID}>
"""

                            await channel.send(msg)

        except Exception as e:
            print("Whale Error:",e)

        await asyncio.sleep(60)


# ---------------- START BOT ---------------- #

@client.event
async def on_ready():

    print("BOT CONNECTED:",client.user)

    client.loop.create_task(crypto_monitor())
    client.loop.create_task(global_monitor())
    client.loop.create_task(commodity_monitor())
    client.loop.create_task(psx_monitor())
    client.loop.create_task(whale_tracker())


client.run(TOKEN)
