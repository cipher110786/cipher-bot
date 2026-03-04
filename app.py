import discord
import aiohttp
import asyncio
import os
from discord.ext import tasks

TOKEN = os.getenv("TOKEN")

CRYPTO_CHANNEL_ID = 1478816867828240626
GLOBAL_CHANNEL_ID = 1478817069415010425
ALERT_ROLE_ID = 1478820285263122572

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ---------------- FETCH ---------------- #

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

# ---------------- CRYPTO DASHBOARD ---------------- #

@tasks.loop(minutes=1)
async def crypto_dashboard():
    await client.wait_until_ready()
    channel = client.get_channel(CRYPTO_CHANNEL_ID)

    async with aiohttp.ClientSession() as session:

        # CoinGecko Prices
        cg_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,solana,ripple&vs_currencies=usd&include_24hr_change=true"
        prices = await fetch_json(session, cg_url)

        # Global Market
        global_url = "https://api.coingecko.com/api/v3/global"
        global_data = await fetch_json(session, global_url)

        # Fear & Greed
        fear_url = "https://api.alternative.me/fng/?limit=1"
        fear_data = await fetch_json(session, fear_url)

        # Funding Rate (Binance)
        funding_url = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT"
        funding_data = await fetch_json(session, funding_url)

    if not prices or not global_data:
        return

    btc = prices["bitcoin"]["usd"]
    eth = prices["ethereum"]["usd"]
    bnb = prices["binancecoin"]["usd"]
    sol = prices["solana"]["usd"]
    xrp = prices["ripple"]["usd"]

    market_cap = global_data["data"]["total_market_cap"]["usd"]
    volume = global_data["data"]["total_volume"]["usd"]

    fear_value = fear_data["data"][0]["value"] if fear_data else "N/A"
    funding_rate = float(funding_data["lastFundingRate"]) * 100 if funding_data else 0

    embed = discord.Embed(
        title="📊 Institutional Crypto Dashboard (Hourly)",
        color=0x00ffcc
    )

    embed.add_field(name="🟡 BTC", value=f"${btc:,}", inline=True)
    embed.add_field(name="🟣 ETH", value=f"${eth:,}", inline=True)
    embed.add_field(name="🟠 BNB", value=f"${bnb:,}", inline=True)
    embed.add_field(name="🟢 SOL", value=f"${sol:,}", inline=True)
    embed.add_field(name="🔵 XRP", value=f"${xrp:,}", inline=True)

    embed.add_field(name="🌍 Market Cap", value=f"${market_cap:,.0f}", inline=False)
    embed.add_field(name="📈 24h Volume", value=f"${volume:,.0f}", inline=False)
    embed.add_field(name="😱 Fear & Greed", value=fear_value, inline=True)
    embed.add_field(name="💸 BTC Funding", value=f"{funding_rate:.4f}%", inline=True)

    embed.set_footer(text="Free Mode • Conservative API Usage")

    await channel.send(f"<@&{ALERT_ROLE_ID}>", embed=embed)

# ---------------- WHALE ALERT ---------------- #

@tasks.loop(minutes=60)
async def whale_alert():
    await client.wait_until_ready()
    channel = client.get_channel(GLOBAL_CHANNEL_ID)

    url = "https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=20"

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)

    if not data:
        return

    whales = [t for t in data if float(t["qty"]) > 10]

    if not whales:
        return

    for trade in whales:
        qty = float(trade["qty"])
        price = float(trade["price"])
        value = qty * price

        msg = (
            f"<@&{ALERT_ROLE_ID}> 🚨 **BTC Whale Trade Detected**\n"
            f"Amount: {qty} BTC\n"
            f"Value: ${value:,.0f}"
        )

        await channel.send(msg)

# ---------------- READY ---------------- #

@client.event
async def on_ready():
    print(f"Bot online as {client.user}")

    test_channel = client.get_channel(CRYPTO_CHANNEL_ID)
    if test_channel:
        await test_channel.send("✅ Free Institutional Bot Connected.")

    crypto_dashboard.start()
    whale_alert.start()

client.run(TOKEN)

