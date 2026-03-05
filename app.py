import discord
import aiohttp
import asyncio
import os
from datetime import datetime
from bs4 import BeautifulSoup

TOKEN = os.getenv("TOKEN")
CMC_API = os.getenv("CMC_API")

ROLE_ID = 1478820285263122572

CHANNELS = {
    "psx": 1478816955971665990,
    "crypto": 1478816867828240626,
    "global": 1478817069415010425,
    "whale": 1478816921649545256,
    "news": 1478816955971665990
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ----------------------------------

async def safe_json(session, url, headers=None, params=None):
    try:
        async with session.get(url, headers=headers, params=params) as r:
            return await r.json()
    except Exception as e:
        print(f"Fetch error {url}: {e}")
        return None

# ----------------------------------
# PSX INDEX + NEWS
# ----------------------------------

async def psx_monitor():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNELS["psx"])

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:

                # KSE100
                data = await safe_json(
                    session,
                    "https://dps.psx.com.pk/indices/KSE100"
                )

                if data and "data" in data:
                    v = data["data"]["value"]
                    c = data["data"]["change"]
                    p = data["data"]["percent_change"]

                    await channel.send(
                        f"📊 **PSX UPDATE**\n"
                        f"KSE100: **{v}**\n"
                        f"Change: {c} ({p}%)\n"
                        f"<@&{ROLE_ID}>"
                    )

                # PSX News
                async with session.get("https://dps.psx.com.pk/news") as r:
                    soup = BeautifulSoup(await r.text(), "html.parser")

                    headlines = [
                        h.text.strip()
                        for h in soup.find_all("h3")[:3]
                    ]

                    if headlines:
                        msg = "\n".join([f"• {h}" for h in headlines])

                        await channel.send(
                            f"📰 **PSX NEWS**\n{msg}\n<@&{ROLE_ID}>"
                        )

            except Exception as e:
                print("PSX Error:", e)

            await asyncio.sleep(3600)

# ----------------------------------
# CRYPTO MARKET (COINMARKETCAP)
# ----------------------------------

async def crypto_market():
    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["crypto"])

    headers = {
        "X-CMC_PRO_API_KEY": CMC_API
    }

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():

            try:

                data = await safe_json(
                    session,
                    "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                    headers=headers,
                    params={"symbol": "BTC,ETH,SOL"}
                )

                if data:

                    btc = data["data"]["BTC"]["quote"]["USD"]["price"]
                    eth = data["data"]["ETH"]["quote"]["USD"]["price"]
                    sol = data["data"]["SOL"]["quote"]["USD"]["price"]

                    await channel.send(
                        f"🪙 **CRYPTO MARKET**\n"
                        f"BTC: ${btc:,.0f}\n"
                        f"ETH: ${eth:,.0f}\n"
                        f"SOL: ${sol:,.0f}\n"
                        f"<@&{ROLE_ID}>"
                    )

            except Exception as e:
                print("Crypto error:", e)

            await asyncio.sleep(1800)

# ----------------------------------
# GLOBAL MARKETS
# ----------------------------------

async def global_market():
    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["global"])

    async with aiohttp.ClientSession() as session:

        while not client.is_closed():

            try:

                url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EGSPC,%5EIXIC,%5EDJI"

                data = await safe_json(session, url)

                if data:

                    r = data["quoteResponse"]["result"]

                    sp = r[0]["regularMarketPrice"]
                    nq = r[1]["regularMarketPrice"]
                    dj = r[2]["regularMarketPrice"]

                    await channel.send(
                        f"🌍 **GLOBAL MARKETS**\n"
                        f"S&P500: {sp}\n"
                        f"NASDAQ: {nq}\n"
                        f"DOW: {dj}\n"
                        f"<@&{ROLE_ID}>"
                    )

            except Exception as e:
                print("Global error:", e)

            await asyncio.sleep(3600)

# ----------------------------------
# WHALE ALERTS
# ----------------------------------

async def whale_alerts():
    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["whale"])

    async with aiohttp.ClientSession() as session:

        while not client.is_closed():

            try:

                url = "https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=50"

                data = await safe_json(session, url)

                if data:

                    for trade in data:

                        value = float(trade["price"]) * float(trade["qty"])

                        if value > 1000000:

                            await channel.send(
                                f"🐋 **WHALE ALERT**\n"
                                f"Large BTC trade detected\n"
                                f"Value: ${value:,.0f}\n"
                                f"<@&{ROLE_ID}>"
                            )

                            await asyncio.sleep(5)

            except Exception as e:
                print("Whale error:", e)

            await asyncio.sleep(120)

# ----------------------------------
# BOT READY
# ----------------------------------

@client.event
async def on_ready():

    print(f"Bot Online: {client.user}")

    client.loop.create_task(psx_monitor())
    client.loop.create_task(crypto_market())
    client.loop.create_task(global_market())
    client.loop.create_task(whale_alerts())

client.run(TOKEN)
