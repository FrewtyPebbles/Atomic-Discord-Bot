from asyncio import sleep
import os
import random
from discord.ext import commands
from discord import app_commands
import discord
from discord.utils import get as server_get
import pymongo
from BotClass import DBBot
import eyed3
import hashlib
from typing import Optional


class Music(commands.Cog):
    def __init__(self, bot:DBBot):
        self.bot = bot
        self.db = bot.db

    async def songs_autocomplete(self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in [x.removesuffix(".mp3") for x in os.listdir('songs')] if current.lower() in choice.lower()
        ]

    @commands.command(name="upload")
    @commands.has_permissions(administrator=True)
    async def upload(self, ctx:commands.Context, *, args:str):
        "Uploads the attached song(s) with the name(s) if provided as arguments"
        song_names = args.split()
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
            m = hashlib.sha256()
            if len(song_names) > an:
                filename = song_names[an].strip('/').strip('.').strip('\\')
                m.update(filename.encode())
                filename_hash = m.hexdigest()
                file = open(f"filechecking/{filename_hash}.mp3", "wb")
                file.write(await attachment.read())
                file.close()
                
                if eyed3.load(f"filechecking/{filename_hash}.mp3") == None:
                    await ctx.send(f"***{filename}*** is not a valid mp3!")
                    os.remove(f"filechecking/{filename_hash}.mp3")
                    return
                os.remove(f"filechecking/{filename_hash}.mp3")
                file = open(f"songs/{filename}.mp3", "wb")
                file.write(await attachment.read())
                file.close()
                song = filename
            else:
                filename = attachment.filename.removesuffix('.mp3').strip('/').strip('.').strip('\\')
                m.update(filename.encode())
                filename_hash = m.hexdigest()
                file = open(f"filechecking/{filename_hash}.mp3", "wb")
                file.write(await attachment.read())
                file.close()
                
                if eyed3.load(f"filechecking/{filename_hash}.mp3") == None:
                    await ctx.send(f"***{filename}*** is not a valid mp3!")
                    os.remove(f"filechecking/{filename_hash}.mp3")
                    return
                file = open(f"songs/{filename}.mp3", "wb")
                file.write(await attachment.read())
                file.close()
                song = filename
            files.append(song)
        embed = discord.Embed(title=f"Added Song{'s' if len(files) > 1 else ''}", description="*For more commands use `!music commands`*", color=16711801)
        for tn, track in enumerate(files):
            embed.add_field(name=f"{tn + 1} - *{track}*", value="", inline=False)
        await ctx.send(embed=embed)
    
    @app_commands.command(name="play")
    @app_commands.autocomplete(song=songs_autocomplete)
    async def play(self, interaction:discord.Interaction, song:Optional[str]):
        if song != None:
            await self.db.queue.update_one(
                {
                    "gid":interaction.guild_id,
                },
                {
                    "$push":{"queue":{"$each":[song],"$position":0}}
                },
                upsert = True)
        voice_channel = interaction.user.voice.channel
        channel = None
        if voice_channel != None:
            channel = voice_channel.name
            vc = await voice_channel.connect()
            await interaction.response.send_message(f"***Atomic*** has joined {channel}")
            queue = await self.get_queue(interaction.guild_id)
            #play every song in queue
            while len(queue["queue"]) > 0:
                await interaction.channel.send(f"***Playing `{queue['queue'][0]}`***")
                await sleep(0.1)
                vc.play(discord.FFmpegPCMAudio(executable="ffmpeg/ffmpeg.exe", source=f"songs/{queue['queue'][0]}.mp3"))
                while vc.is_playing():
                    await sleep(0.1)
                await self.db.queue.update_one(
                    {
                        "gid":interaction.guild_id,
                    },
                    {
                        "$pop":{"queue":-1}
                    },
                    upsert = True)
                queue = await self.get_queue(interaction.guild_id)

            await vc.disconnect()
        else:
            await interaction.channel.send(str(interaction.user.name) + "is not in a channel.")

    
    @app_commands.command(name="queue")
    @app_commands.autocomplete(song=songs_autocomplete)
    async def queue(self, interaction:discord.Interaction, song:str):
        if os.path.isfile(f"songs/{song}.mp3"):
            await interaction.response.send_message(f"***Added `{song}` to queue***")
            await self.db.queue.update_one(
            {
                "gid":interaction.guild_id,
            },
            {
                "$push":{"queue":song}
            },
            upsert = True)
        else:
            await interaction.response.send_message("***The song you specified was not a valid song, please try again***")
        
    @app_commands.command(name="queueall")
    async def queueall(self, interaction:discord.Interaction):
        songs = [x.removesuffix(".mp3") for x in os.listdir('songs')]
        await self.db.queue.update_one(
            {
                "gid":interaction.guild_id,
            },
            {
                "$push":{"queue":{"$each":[*songs]}}
            },
            upsert = True)
        await interaction.response.send_message(f"***Added `{'`, `'.join(songs)}` to queue***")

    async def get_queue(self, gid:int) -> dict[str,int|list[str]]:
        queue = await self.db.queue.find_one({"gid":gid})
        if queue == None:
            await self.db.queue.update_one(
            {
                "gid":gid,
            },
            {
                "queue":[]
            },
            upsert = True)
            return {
                "gid":gid,
                "queue":[]
            }
        else:
            return queue
        

    @app_commands.command(name="shuffle")
    async def shuffle(self, interaction:discord.Interaction):
        queue = {"gid":interaction.guild_id,"queue":[]}
        queue = await self.get_queue(interaction.guild_id)
        random.shuffle(queue["queue"])
        await self.db.queue.update_one(
            {
                "gid":interaction.guild_id,
            },
            {
                "queue":queue["queue"]
            },
            upsert = True)
        await interaction.response.send_message(f"***The Queue has been shuffled***")
    
    @app_commands.command(name="queueclear")
    async def queueclear(self, interaction:discord.Interaction):
        await self.db.queue.update_one(
            {
                "gid":interaction.guild_id,
            },
            {
                "$set":{"queue":[]}
            },
            upsert = True)
        await interaction.response.send_message(f"***The Queue has been cleared***")

    @app_commands.command(name="music")
    @app_commands.choices(option=[
        app_commands.Choice(name="Help", value="help"),
        app_commands.Choice(name="Commands", value="commands"),
        app_commands.Choice(name="List Songs", value="list"),
        app_commands.Choice(name="Queue", value="queue"),
    ])
    async def music(self, interaction:discord.Interaction, option:Optional[app_commands.Choice[str]]):
        "A music help command"
        arg1 = option
        if not arg1:
            queue = await self.get_queue(interaction.guild_id)
            if len(queue['queue']) > 0:
                embed = discord.Embed(title=f"Currently Playing: ***{queue['queue'][0]}***", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title=f"No Song Currently Playing", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
                await interaction.response.send_message(embed=embed)
        
        elif arg1.value == "help" or arg1.value == "commands":
            embed = discord.Embed(title=f"Music Help", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
            embed.add_field(name=f"***!music list***", value="Lists all songs available to play.", inline=False)
            embed.add_field(name=f"***!music queue***", value="Lists all songs in the queue.", inline=False)
            embed.add_field(name=f"***!music commands***", value="Shows this menu.", inline=False)
            embed.add_field(name=f"***!music help***", value="Shows this menu.", inline=False)
            embed.add_field(name=f"***!play song_name***", value="Plays all music with the provided song at the front of the queue.", inline=False)
            embed.add_field(name=f"***!play***", value="Plays all music in queue.", inline=False)
            embed.add_field(name=f"***!queue song_name1 song_name2...***", value="Adds music to the end of the queue.", inline=False)
            embed.add_field(name=f"***!upload song_name1 song_name2...***", value="Adds attached mp3 file(s) to the bot's filesystem using the name(s) provided as arguments.", inline=False)
            embed.add_field(name=f"***!queueall***", value="Adds all music to the end of the queue.", inline=False)
            embed.add_field(name=f"***!shuffle***", value="Shuffles all songs in the queue.", inline=False)
            await interaction.response.send_message(embed=embed)

        elif arg1.value == "list":
            songs = [x.removesuffix(".mp3") for x in os.listdir('songs')]
            embed = discord.Embed(title=f"Song List", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
            for sn, song in enumerate(songs):
                embed.add_field(name=f"{sn + 1} - *{song}*", value="", inline=False)
            await interaction.response.send_message(embed=embed)
        
        elif arg1.value == "queue":
            songs = []
            queue = await self.get_queue(interaction.guild_id)
            songs = queue["queue"]
            embed = discord.Embed(title=f"Song Queue", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
            for sn, song in enumerate(songs):
                embed.add_field(name=f"{sn+1} - *{song}*", value="", inline=False)
            await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Music(client))