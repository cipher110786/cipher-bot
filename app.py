import discord
import aiohttp
import asyncio
import os
import json

TOKEN = os.getenv("TOKEN")
CMC_API = os.getenv("CMC_API")

ROLE_ID = 1478820285263122572

CHANNELS = {
    "psx": 1478816955971665990,
    "crypto": 1478816867828240626,
    "global": 1478817069415010425,
    "commodity": 1478816867828240626,
    "whale": 1478816921649545256
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ---------------- HELPER ---------------- #

async def fetch_json(session, url, headers=None, params=None):

    try:

        async with session.get(url, headers=headers, params=params) as r:

            text = await r.text()

            try:
                return json.loads(text)
            except:
                print("JSON parse error:", url)
                return None

    except Exception as e:

        print("Fetch error", url, e)
        return None


# ---------------- PSX MONITOR ---------------- #

async def psx_monitor():

    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["psx"])

    async with aiohttp.ClientSession() as session:

        while True:

            try:

                url = "https://dps.psx.com.pk/indices/KSE100"

                async with session.get(url, headers=HEADERS) as r:

                    text = await r.text()

                if "data" not in text:
                    print("PSX returned HTML")
                    await asyncio.sleep(3600)
                    continue

                data = json.loads(text)

                val = data["data"]["value"]
                change = data["data"]["change"]
                pct = data["data"]["percent_change"]

                msg = f"""
📊 **PSX MARKET**

KSE100: {val}
Change: {change} ({pct}%)

<@&{ROLE_ID}>
"""

                await channel.send(msg)

            except Exception as e:

                print("PSX Error:", e)

            await asyncio.sleep(7200)


# ---------------- CRYPTO (CoinMarketCap) ---------------- #

async def crypto_monitor():

    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["crypto"])

    headers = {
        "X-CMC_PRO_API_KEY": CMC_API
    }

    async with aiohttp.ClientSession() as session:

        while True:

            try:

                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

                params = {
                    "symbol": "BTC,ETH,SOL"
                }

                data = await fetch_json(session, url, headers=headers, params=params)

                if not data:
                    await asyncio.sleep(1800)
                    continue

                btc = data["data"]["BTC"]["quote"]["USD"]["price"]
                eth = data["data"]["ETH"]["quote"]["USD"]["price"]
                sol = data["data"]["SOL"]["quote"]["USD"]["price"]

                msg = f"""
🪙 **CRYPTO MARKET**

BTC: ${btc:,.0f}
ETH: ${eth:,.0f}
SOL: ${sol:,.0f}

<@&{ROLE_ID}>
"""

                await channel.send(msg)

            except Exception as e:

                print("Crypto Error:", e)

            await asyncio.sleep(1800)


# ---------------- GLOBAL MARKETS ---------------- #

async def global_monitor():

    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["global"])

    async with aiohttp.ClientSession() as session:

        while True:

            try:

                url = "https://query1.finance.yahoo.com/v7/finance/quote"

                params = {
                    "symbols": "^GSPC,^IXIC,^DJI"
                }

                async with session.get(url, headers=HEADERS, params=params) as r:

                    text = await r.text()

                if "quoteResponse" not in text:
                    print("Yahoo blocked request")
                    await asyncio.sleep(3600)
                    continue

                data = json.loads(text)

                res = data["quoteResponse"]["result"]

                sp = res[0]["regularMarketPrice"]
                nas = res[1]["regularMarketPrice"]
                dow = res[2]["regularMarketPrice"]

                msg = f"""
🌍 **GLOBAL MARKETS**

S&P500: {sp}
NASDAQ: {nas}
DOW: {dow}

<@&{ROLE_ID}>
"""

                await channel.send(msg)

            except Exception as e:

                print("Global Error:", e)

            await asyncio.sleep(7200)


# ---------------- COMMODITIES ---------------- #

async def commodity_monitor():

    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["commodity"])

    async with aiohttp.ClientSession() as session:

        while True:

            try:

                gold = await fetch_json(session, "https://api.coinbase.com/v2/prices/XAU-USD/spot")

                if gold is None or "data" not in gold:
                    print("Gold API error")
                    await asyncio.sleep(3600)
                    continue

                gold_price = gold["data"]["amount"]

                msg = f"""
🛢 **COMMODITY**

Gold: ${gold_price}

<@&{ROLE_ID}>
"""

                await channel.send(msg)

            except Exception as e:

                print("Commodity Error:", e)

            await asyncio.sleep(7200)


# ---------------- WHALE ALERT ---------------- #

async def whale_tracker():

    await client.wait_until_ready()

    channel = client.get_channel(CHANNELS["whale"])

    async with aiohttp.ClientSession() as session:

        while True:

            try:

                url = "https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=20"

                data = await fetch_json(session, url)

                if not data:
                    await asyncio.sleep(60)
                    continue

                for t in data:

                    price = float(t["price"])
                    qty = float(t["qty"])

                    usd_val = price * qty

                    if usd_val > 750000:

                        msg = f"""
🐋 **WHALE ALERT**

BTC Trade: ${usd_val:,.0f}

<@&{ROLE_ID}>
"""

                        await channel.send(msg)

                        await asyncio.sleep(5)

            except Exception as e:

                print("Whale Error:", e)

            await asyncio.sleep(60)


# ---------------- BOT READY ---------------- #

@client.event
async def on_ready():

    print("BOT CONNECTED:", client.user)

    client.loop.create_task(psx_monitor())
    client.loop.create_task(crypto_monitor())
    client.loop.create_task(global_monitor())
    client.loop.create_task(commodity_monitor())
    client.loop.create_task(whale_tracker())


client.run(TOKEN)
