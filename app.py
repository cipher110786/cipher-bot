import discord
import aiohttp
import asyncio
import os
from discord.ext import tasks

TOKEN = os.getenv("TOKEN")

# ================= CONFIG =================

CRYPTO_CHANNEL_ID = 1478816867828240626
METALS_CHANNEL_ID = 1478816867828240626
PSX_CHANNEL_ID = 1478816955971665990
GLOBAL_CHANNEL_ID = 1478817069415010425
WHALE_CHANNEL_ID = 1478816921649545256

ALERT_ROLE_ID = 1478820285263122572

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ==========================================

async def fetch_json(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            if response.status != 200:
                print("HTTP Error:", response.status, url)
                return None
            return await response.json()
    except Exception as e:
        print("Fetch Error:", e)
        return None


# ================= CRYPTO =================

@tasks.loop(minutes=5)
async def crypto_update():
    await client.wait_until_ready()
    channel = client.get_channel(CRYPTO_CHANNEL_ID)

    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)

    if not data:
        return

    btc = data["bitcoin"]["usd"]
    eth = data["ethereum"]["usd"]

    embed = discord.Embed(
        title="💰 Crypto Market Update",
        color=0x00ffcc
    )
    embed.add_field(name="🟡 BTC", value=f"${btc:,}", inline=True)
    embed.add_field(name="🟣 ETH", value=f"${eth:,}", inline=True)
    embed.set_footer(text="Source: CoinGecko")

    await channel.send(embed=embed)


# ================= METALS =================

@tasks.loop(minutes=10)
async def metals_update():
    await client.wait_until_ready()
    channel = client.get_channel(METALS_CHANNEL_ID)

    url = "https://api.metals.live/v1/spot"

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)

    if not data:
        return

    prices = {list(item.keys())[0]: list(item.values())[0] for item in data}

    gold = prices.get("gold")
    silver = prices.get("silver")
    copper = prices.get("copper")

    embed = discord.Embed(
        title="🏅 Metals Market",
        color=0xffcc00
    )
    embed.add_field(name="🥇 Gold", value=f"${gold}" if gold else "N/A")
    embed.add_field(name="🥈 Silver", value=f"${silver}" if silver else "N/A")
    embed.add_field(name="🟤 Copper", value=f"${copper}" if copper else "N/A")

    await channel.send(embed=embed)


# ================= PSX =================

@tasks.loop(minutes=15)
async def psx_update():
    await client.wait_until_ready()
    channel = client.get_channel(PSX_CHANNEL_ID)

    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EKSE"

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)

    if not data:
        return

    try:
        result = data["quoteResponse"]["result"][0]
        price = result["regularMarketPrice"]
        change = result["regularMarketChangePercent"]

        embed = discord.Embed(
            title="📈 PSX (KSE-100)",
            color=0x00ff00 if change >= 0 else 0xff0000
        )
        embed.add_field(name="Index", value=f"{price:,}")
        embed.add_field(name="Change", value=f"{change:.2f}%")

        await channel.send(embed=embed)

    except:
        print("KSE format changed")


# ================= GLOBAL SNAPSHOT =================

@tasks.loop(minutes=20)
async def global_snapshot():
    await client.wait_until_ready()
    channel = client.get_channel(GLOBAL_CHANNEL_ID)

    url = "https://api.coingecko.com/api/v3/global"

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)

    if not data:
        return

    market_cap = data["data"]["total_market_cap"]["usd"]
    volume = data["data"]["total_volume"]["usd"]

    embed = discord.Embed(
        title="🌍 Global Crypto Snapshot",
        color=0x3498db
    )
    embed.add_field(name="Market Cap", value=f"${market_cap:,.0f}")
    embed.add_field(name="24h Volume", value=f"${volume:,.0f}")

    await channel.send(embed=embed)


# ================= WHALE ALERT =================

@tasks.loop(minutes=7)
async def whale_alert():
    await client.wait_until_ready()
    channel = client.get_channel(WHALE_CHANNEL_ID)

    url = "https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=5"

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)

    if not data:
        return

    large_trades = [trade for trade in data if float(trade["qty"]) > 5]

    if not large_trades:
        return

    for trade in large_trades:
        qty = float(trade["qty"])
        price = float(trade["price"])
        value = qty * price

        message = (
            f"<@&{ALERT_ROLE_ID}> 🚨 **Whale Alert**\n"
            f"BTC Trade: {qty} BTC\n"
            f"Value: ${value:,.0f}"
        )

        await channel.send(message)


# ================= READY =================

@client.event
async def on_ready():
    print(f"Bot online as {client.user}")

    crypto_update.start()
    metals_update.start()
    psx_update.start()
    global_snapshot.start()
    whale_alert.start()



client.run(TOKEN)
