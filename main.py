from asyncio import sleep
import asyncio
import os
import discord
from discord.utils import get as server_get
from BotClass import DBBot
from dotenv import load_dotenv
import logging

#ATOMIC
VER = "0.1.0"

load_dotenv()

intents = discord.Intents.all()
intents.message_content = True
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

bot = DBBot(command_prefix = "!", intents=intents)

async def load_exts():
    for f in os.listdir("./cogs"):
        if f.endswith(".py"):
            await bot.load_extension("cogs." + f[:-3])

async def main():
    await load_exts()

asyncio.run(main())
bot.run(os.getenv("DISCORD_TOKEN"), log_handler=handler)