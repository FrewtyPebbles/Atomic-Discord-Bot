from asyncio import sleep
import os
import random
from discord.ext import commands
import discord
from discord.utils import get as server_get
from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient


class RequiresDB(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        mongo_client = AsyncIOMotorClient(getenv("DB_HOST"))
        self.db = mongo_client[getenv("DB_NAME")]

    def rgbtoint32(self, rgb):
        color = 0
        for c in rgb[::-1]:
            color = (color<<8) + c
            # Do not forget parenthesis.
            # color<< 8 + c is equivalent of color << (8+c)
        return color

    #START ROLES

    @commands.command()
    async def roleprompt(self, ctx:commands.Context, red:int, green:int, blue:int, *, desc_and_fields:str):
        df_split = desc_and_fields.splitlines()
        title = df_split[0]
        df_split.pop(0)
        desc = df_split[0]
        df_split.pop(0)
        it = iter(df_split)
        raw_fields = [*zip(it, it)]
        print(self.rgbtoint32([red,green,blue]))
        embed = discord.Embed(title=title, description=desc, color=self.rgbtoint32([red,green,blue]))
        emoji_role_pairs:list[list[str, str]] = []
        for raw_raw_name, raw_value in raw_fields:
            raw_emoji, raw_name = raw_raw_name.split("$$$")
            emoji = raw_emoji.strip()
            role = raw_name.strip()
            value = raw_value.strip()
            embed.add_field(name=f"{emoji} - {role}", value=value, inline=False)
            print(f"{emoji} - {role}")
            emoji_role_pairs.append([emoji, role])

        msg = await ctx.send(embed=embed)
        for r_emoji, r_role in emoji_role_pairs:
            await msg.add_reaction(r_emoji)
        
        await self.db.role_messages.update_one(
            {
                "gid":ctx.guild.id,
                "channelid":ctx.channel.id,
                "messageid":msg.id
            },
            {
                "$set":{"roles":emoji_role_pairs}
            },
            upsert = True)
        await ctx.message.delete()


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction:discord.RawReactionActionEvent):
        role_msg = await self.db.role_messages.find_one({
            "gid":reaction.guild_id,
            "channelid":reaction.channel_id,
            "messageid":reaction.message_id
        })
        # Return if the message is not in the db
        if role_msg == None:
            return
        
        valid_reaction = False
        for rolereaction, role in role_msg["roles"]:
            print(f"{str(reaction.emoji) == str(rolereaction)}")
            if str(reaction.emoji) == str(rolereaction):
                Role = discord.utils.get(reaction.member.guild.roles, name=role)
                await reaction.member.add_roles(Role)
                valid_reaction = True

        if not valid_reaction:
            Emoji:discord.Reaction = discord.utils.get(reaction.member.guild.emojis, id=reaction.emoji.id)
            Emoji.remove()

    #END ROLES

    
    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        bot_cmds = server_get(guild.categories, name="Atomic")
        if bot_cmds == None:
            Roles_category = await guild.create_category("Mission Control")
            Rules_ch = await guild.create_text_channel(name="Rules", category=Roles_category)
            Announcements_ch = await guild.create_text_channel(name="Announcements", category=Roles_category)
            Roles_ch = await guild.create_text_channel(name="Roles", category=Roles_category)
            atomic_category = await guild.create_category("Atomic")
            bot_commands_ch = await guild.create_text_channel(name="Bot-Commands", category=atomic_category)
            VOIP_category = await guild.create_category("Voice Channels")
            VOIP_bot_commands_ch = await guild.create_text_channel(name="Bot-Commands", category=VOIP_category)
            VOIP_create_ch = await guild.create_voice_channel(name="Create A Voice Channel", category=VOIP_category)
        
        #insert guild into db if not exist
        guild_in_db = len(await self.db.guild.find({'gid':guild.id}).to_list(None))
        if guild_in_db == 0:
            print(f"""ADDING GUILD TO DB:\n{{
    "gid":{guild.id},
    "name":{guild.name},
    "description":{guild.description},
    "premium_tier":{guild.premium_tier}
}}""")
            await self.db.guild.insert_one(
            {
                "gid":guild.id,
                "name":guild.name,
                "description":guild.description,
                "premium_tier":guild.premium_tier
            })

    @commands.command(help="THIS IS MAINLY A DEVELOPMENT COMMAND AND SHOULD ONLY BE USED IF THE BOT FAILED TO CONFIGURE THE SERVER WHEN JOINING THE SERVER.")
    async def CONFIGURE(self, ctx:commands.Context):
        await ctx.send("***WARNING: THIS IS MAINLY A DEVELOPMENT COMMAND AND SHOULD ONLY BE USED IF THE BOT FAILED TO CONFIGURE THE SERVER WHEN JOINING THE SERVER.***")
        await ctx.send("***Configuring...***")
        await self.on_guild_join(ctx.guild)
        await ctx.send("***Configuration Complete!***")

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
        return await self.db.queue.find_one({"gid":ctx.guild.id})

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
    await client.add_cog(RequiresDB(client))