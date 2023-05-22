from asyncio import sleep
import os
import random
from discord.ext import commands
import discord
from discord.utils import get as server_get
import pymongo
from BotClass import DBBot
import eyed3
import hashlib



class Music(commands.Cog):
    def __init__(self, bot:DBBot):
        self.bot = bot
        self.db = bot.db

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
            m = hashlib.sha256()
            if len(args) > an:
                filename = args[an].strip('/').strip('.').strip('\\')
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
    
    @commands.command()
    async def play(self, ctx:commands.Context, song:str | None = None):
        if song != None:
            await self.db.queue.update_one(
                {
                    "gid":ctx.guild.id,
                },
                {
                    "$push":{"queue":{"$each":[song],"$position":0}}
                },
                upsert = True)
        voice_channel = ctx.author.voice.channel
        channel = None
        if voice_channel != None:
            channel = voice_channel.name
            vc = await voice_channel.connect()

            queue = await self.get_queue(ctx)
            #play every song in queue
            while len(queue["queue"]) > 0:
                await ctx.send(f"***Playing `{queue['queue'][0]}`***")
                await sleep(0.1)
                vc.play(discord.FFmpegPCMAudio(executable="ffmpeg/ffmpeg.exe", source=f"songs/{queue['queue'][0]}.mp3"))
                while vc.is_playing():
                    await sleep(0.1)
                await self.db.queue.update_one(
                    {
                        "gid":ctx.guild.id,
                    },
                    {
                        "$pop":{"queue":-1}
                    },
                    upsert = True)
                queue = await self.get_queue(ctx)

            await vc.disconnect()
        else:
            await ctx.send(str(ctx.author.name) + "is not in a channel.")

    @commands.command()
    async def queue(self, ctx:commands.Context, *songs:str):
        
        if all([os.path.isfile(f"songs/{song}.mp3") for song in songs]):
            await ctx.send(f"***Added `{'`, `'.join(songs)}` to queue***")
            await self.db.queue.update_one(
            {
                "gid":ctx.guild.id,
            },
            {
                "$push":{"queue":{"$each":[*songs]}}
            },
            upsert = True)
        else:
            await ctx.send("***One or more of the songs you specified were not valid songs, please try again***")
        
    @commands.command()
    async def queueall(self, ctx:commands.Context):
        songs = [x.removesuffix(".mp3") for x in os.listdir('songs')]
        await self.db.queue.update_one(
            {
                "gid":ctx.guild.id,
            },
            {
                "$push":{"queue":{"$each":[*songs]}}
            },
            upsert = True)
        await ctx.send(f"***Added `{'`, `'.join(songs)}` to queue***")

    async def get_queue(self, ctx:commands.Context) -> dict[str,int|list[str]]:
        queue = await self.db.queue.find_one({"gid":ctx.guild.id})
        if queue == None:
            await self.db.queue.update_one(
            {
                "gid":ctx.guild.id,
            },
            {
                "queue":[]
            },
            upsert = True)
            return {
                "gid":ctx.guild.id,
                "queue":[]
            }
        else:
            return queue
        

    @commands.command()
    async def shuffle(self, ctx:commands.Context):
        queue = {"gid":ctx.guild.id,"queue":[]}
        queue = await self.get_queue(ctx)
        random.shuffle(queue["queue"])
        await self.db.queue.update_one(
            {
                "gid":ctx.guild.id,
            },
            {
                "queue":queue["queue"]
            },
            upsert = True)
        await ctx.send(f"***The Queue has been shuffled***")
    
    @commands.command()
    async def queueclear(self, ctx:commands.Context):
        await self.db.queue.update_one(
            {
                "gid":ctx.guild.id,
            },
            {
                "$set":{"queue":[]}
            },
            upsert = True)
        await ctx.send(f"***The Queue has been cleared***")

    @commands.command(help="A music help command")
    async def music(self, ctx:commands.Context, arg1:str = None, *arg2:str):
        if not arg1 and len(arg2) == 0:
            queue = await self.get_queue(ctx)
            if len(queue['queue']) > 0:
                embed = discord.Embed(title=f"Currently Playing: ***{queue['queue'][0]}***", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title=f"No Song Currently Playing", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
                await ctx.send(embed=embed)
        
        elif arg1 == "help" or arg1 == "commands":
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
            await ctx.send(embed=embed)

        elif arg1 == "list":
            songs = [x.removesuffix(".mp3") for x in os.listdir('songs')]
            embed = discord.Embed(title=f"Song List", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
            for sn, song in enumerate(songs):
                embed.add_field(name=f"{sn + 1} - *{song}*", value="", inline=False)
            await ctx.send(embed=embed)
        
        elif arg1 == "queue":
            songs = []
            queue = await self.get_queue(ctx)
            songs = queue["queue"]
            embed = discord.Embed(title=f"Song Queue", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
            for sn, song in enumerate(songs):
                embed.add_field(name=f"{sn+1} - *{song}*", value="", inline=False)
            await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(Music(client))