import discord
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

CRYPTO_CHANNEL_ID = int(os.getenv("CRYPTO_CHANNEL_ID", "0"))
WHALE_CHANNEL_ID = int(os.getenv("WHALE_CHANNEL_ID", "0"))
PSX_CHANNEL_ID = int(os.getenv("PSX_CHANNEL_ID", "0"))
CMC_CHANNEL_ID = int(os.getenv("CMC_CHANNEL_ID", "0"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def crypto_updates():
    await client.wait_until_ready()
    channel = client.get_channel(CRYPTO_CHANNEL_ID)

    while not client.is_closed():
        if channel:
            await channel.send("🚀 Crypto Market Update: BTC & ETH moving!")
        await asyncio.sleep(1800)


async def whale_updates():
    await client.wait_until_ready()
    channel = client.get_channel(WHALE_CHANNEL_ID)

    while not client.is_closed():
        if channel:
            await channel.send("🐋 Whale Alert: Large crypto transfer detected!")
        await asyncio.sleep(1800)


async def psx_updates():
    await client.wait_until_ready()
    channel = client.get_channel(PSX_CHANNEL_ID)

    while not client.is_closed():
        if channel:
            await channel.send("📈 PSX Update: Pakistan Stock Exchange activity.")
        await asyncio.sleep(1800)


async def cmc_updates():
    await client.wait_until_ready()
    channel = client.get_channel(CMC_CHANNEL_ID)

    while not client.is_closed():
        if channel:
            await channel.send("💰 CoinMarketCap Update: Top crypto rankings updated.")
        await asyncio.sleep(1800)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    client.loop.create_task(crypto_updates())
    client.loop.create_task(whale_updates())
    client.loop.create_task(psx_updates())
    client.loop.create_task(cmc_updates())


client.run(TOKEN)
