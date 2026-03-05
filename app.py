import discord
import aiohttp
import asyncio
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TOKEN")
CMC_API = os.getenv("CMC_API_KEY")
ALPHA = os.getenv("ALPHA_API_KEY")

ROLE_ID = 1478820285263122572

CHANNELS = {
    "psx":1478816955971665990,
    "crypto":1478816867828240626,
    "global":1478817069415010425,
    "commodities":1478816867828240626,
    "whale":1478816921649545256
}

HEADERS={"User-Agent":"Mozilla/5.0"}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ---------------- CRYPTO ---------------- #

async def crypto_monitor():

    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["crypto"])

    url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_API}
    params={"symbol":"BTC,ETH,SOL,BNB,XRP"}

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


# ---------------- GLOBAL ---------------- #

async def global_monitor():

    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["global"])

    while not client.is_closed():

        try:
            async with aiohttp.ClientSession() as session:

                sp=f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=SPY&apikey={ALPHA}"
                dj=f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=DIA&apikey={ALPHA}"
                nq=f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=QQQ&apikey={ALPHA}"

                async with session.get(sp) as r1:
                    sp_data=await r1.json()

                async with session.get(dj) as r2:
                    dj_data=await r2.json()

                async with session.get(nq) as r3:
                    nq_data=await r3.json()

                spx=sp_data["Global Quote"]["05. price"]
                dow=dj_data["Global Quote"]["05. price"]
                nas=nq_data["Global Quote"]["05. price"]

                msg=f"""
🌍 **GLOBAL MARKETS**

S&P500 ETF : {spx}
Dow Jones ETF : {dow}
Nasdaq ETF : {nas}

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

                url="https://api.metals.live/v1/spot"

                async with session.get(url) as r:
                    data=await r.json()

                gold=data[0]["gold"]
                silver=data[1]["silver"]

                msg=f"""
🛢 **COMMODITIES**

🥇 Gold : ${gold}
🥈 Silver : ${silver}

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

                url="https://www.psx.com.pk/"

                async with session.get(url,headers=HEADERS) as r:

                    html=await r.text()
                    soup=BeautifulSoup(html,"html.parser")

                    val=soup.find("div",class_="market-value")

                    if val:

                        index=val.text.strip()

                        msg=f"""
🇵🇰 **PAKISTAN STOCK EXCHANGE**

KSE-100 Index : {index}

<@&{ROLE_ID}>
"""
                        await channel.send(msg)

                    else:
                        print("PSX structure changed")

        except Exception as e:
            print("PSX Error:",e)

        await asyncio.sleep(3600)


# ---------------- WHALE ---------------- #

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
🐋 **BTC WHALE TRADE**

Value : ${usd:,.0f}

<@&{ROLE_ID}>
"""
                        await channel.send(msg)

        except Exception as e:
            print("Whale Error:",e)

        await asyncio.sleep(60)


# ---------------- BOT START ---------------- #

@client.event
async def on_ready():

    print("BOT CONNECTED:",client.user)

    client.loop.create_task(crypto_monitor())
    client.loop.create_task(global_monitor())
    client.loop.create_task(commodity_monitor())
    client.loop.create_task(psx_monitor())
    client.loop.create_task(whale_tracker())

client.run(TOKEN)
