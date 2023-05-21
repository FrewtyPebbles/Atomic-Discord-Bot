import random
from discord.ext import commands
import discord
from discord.utils import get as server_get
import pymongo


class Music(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command(help="Uploads the attached song(s) with the name(s) if provided as arguments")
    @commands.has_permissions(administrator=True)
    async def upload(self, ctx:commands.Context, *args:str):
        if len(ctx.message.attachments) == 0:
            await ctx.send("***No songs were attached***")
            return
        if not all([attachment.filename.endswith(".mp3") for attachment in ctx.message.attachments]):
            await ctx.send("***One or more of your songs is not an mp3 file.***")
            return
        
        # upload files
        files = []
        for an, attachment in enumerate(ctx.message.attachments):
            song = ""
            if len(args) > an:
                file = open(f"songs/{args[an]}.mp3", "wb")
                file.write(await attachment.read())
                file.close()
                song = args[an]
            else:
                file = open(f"songs/{attachment.filename.removesuffix('.mp3')}.mp3", "wb")
                file.write(await attachment.read())
                file.close()
                song = attachment.filename.removesuffix('.mp3')
            files.append(song)
        embed = discord.Embed(title=f"Added Song{'s' if len(files) > 1 else ''}", description="*For more commands use `!music commands`*", color=16711801)
        for tn, track in enumerate(files):
            embed.add_field(name=f"{tn + 1} - *{track}*", value="", inline=False)
        await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(Music(client))