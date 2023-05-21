from discord.ext import commands
import discord
from discord.utils import get as server_get

class Menus(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

async def setup(client):
    await client.add_cog(Menus(client))