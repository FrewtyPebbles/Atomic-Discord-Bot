from asyncio import sleep
import asyncio
import os
import discord
from discord.utils import get as server_get
from discord.ext import commands
from dotenv import load_dotenv
import logging

#ATOMIC
VER = "0.1.0"

load_dotenv()

intents = discord.Intents.all()
intents.message_content = True
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

bot = commands.Bot(command_prefix = "!", intents=intents)

async def load_exts():
    for f in os.listdir("./cogs"):
        if f.endswith(".py"):
            await bot.load_extension("cogs." + f[:-3])

async def main():
    await load_exts()

asyncio.run(main())
bot.run(os.getenv("DISCORD_TOKEN"), log_handler=handler)

##OLD CODE

# intents = discord.Intents.default()
# intents.message_content = True

# bot = commands.Bot(command_prefix="!", intents=intents)
# global_guild_data:dict[int,dict[str, list[str]|any]] = {}

# @bot.event
# async def on_ready():
#     print(f'We have logged in as {bot.user}')

# @bot.event
# async def on_guild_join(guild:discord.Guild):
#     bot_cmds = server_get(guild.categories, name="Atomic")
#     if bot_cmds == None:
#         Roles_category = await guild.create_category("Mission Control")
#         Rules_ch = await guild.create_text_channel(name="Rules", category=Roles_category)
#         Announcements_ch = await guild.create_text_channel(name="Announcements", category=Roles_category)
#         Roles_ch = await guild.create_text_channel(name="Roles", category=Roles_category)
#         atomic_category = await guild.create_category("Atomic")
#         bot_commands_ch = await guild.create_text_channel(name="Bot-Commands", category=atomic_category)
#         VOIP_category = await guild.create_category("Voice Channels")
#         VOIP_bot_commands_ch = await guild.create_text_channel(name="Bot-Commands", category=VOIP_category)
#         VOIP_create_ch = await guild.create_voice_channel(name="Create A Voice Channel", category=VOIP_category)

# @bot.command(help="THIS IS MAINLY A DEVELOPMENT COMMAND AND SHOULD ONLY BE USED IF THE BOT FAILED TO CONFIGURE THE SERVER WHEN JOINING THE SERVER.")
# async def CONFIGURE(ctx:commands.Context):
#     await ctx.send("***WARNING: THIS IS MAINLY A DEVELOPMENT COMMAND AND SHOULD ONLY BE USED IF THE BOT FAILED TO CONFIGURE THE SERVER WHEN JOINING THE SERVER.***")
#     await ctx.send("***Configuring...***")
#     await on_guild_join(ctx.guild)
#     await ctx.send("***Configuration Complete!***")

# #Voice Channel Creator
# @bot.event
# async def on_voice_state_update(member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
#     if before.channel == None and after.channel != None:
#         #joins
#         if after.channel.name == "Create A Voice Channel":
#             vc_category = server_get(member.guild.categories, name="Voice Channels")
#             vc = await member.guild.create_voice_channel(f"Voice - {len(member.guild.voice_channels) - 1}", category=vc_category)
#             await member.move_to(vc)
#     elif before.channel != None and after.channel == None:
#         #leaves
#         if before.channel.name != "Create A Voice Channel" and before.channel.category.name == "Voice Channels":
#             if len(before.channel.members) <= 0:
#                 await before.channel.delete()
#     elif before.channel != None and after.channel != None:
#         #switches channels
#         if before.channel.name != "Create A Voice Channel" and before.channel.category.name == "Voice Channels":
#             if len(before.channel.members) <= 0:
#                 await before.channel.delete()
#         if after.channel.name == "Create A Voice Channel":
#             vc_category = server_get(member.guild.categories, name="Voice Channels")
#             vc = await member.guild.create_voice_channel(f"Voice - {len(member.guild.voice_channels) - 1}", category=vc_category)
#             await member.move_to(vc)

# @bot.command()
# async def resize(ctx:commands.Context, people):
#     vc = ctx.author.voice.channel
#     if vc:
#         await vc.edit(user_limit=int(people))
#         await ctx.send(f"Resizing ***{vc.name}*** to *{people}*")
#     else:
#         await ctx.send("You do not appear to be in a voice channel.")

# @bot.command()
# @commands.has_permissions(administrator=True)
# async def purge(ctx:commands.Context, number:int|str = 1):
#     if number == "all":
#         deleted = await ctx.channel.purge()
#         await ctx.send(f'Deleted *{len(deleted)}* message{"s" if len(deleted) > 1 else ""}', delete_after=5)
#         return
#     number = int(number)
#     deleted = await ctx.channel.purge(limit=number)
#     await ctx.send(f'Deleted *{len(deleted)}* message{"s" if len(deleted) > 1 else ""}', delete_after=5)

# #MUSIC
# @bot.command()
# async def play(ctx:commands.Context, song:str | None = None):
#     if song != None:
#         if ctx.guild.id in global_guild_data.keys():
#             global_guild_data[ctx.guild.id] = {"queue":[song, *global_guild_data[ctx.guild.id]]}
#         else:
#             global_guild_data[ctx.guild.id]["queue"] = [song]
#     voice_channel = ctx.author.voice.channel
#     channel = None
#     if voice_channel != None:
#         channel = voice_channel.name
#         vc = await voice_channel.connect()

#         #play every song in queue
#         while len(global_guild_data[ctx.guild.id]["queue"]) > 0:
#             await ctx.send(f"***Playing `{global_guild_data[ctx.guild.id]['queue'][0]}`***")
#             await sleep(0.1)
#             vc.play(discord.FFmpegPCMAudio(executable="ffmpeg/ffmpeg.exe", source=f"songs/{global_guild_data[ctx.guild.id]['queue'][0]}.mp3"))
#             while vc.is_playing():
#                 await sleep(0.1)
#             global_guild_data[ctx.guild.id]["queue"].pop(0)

#         await vc.disconnect()
#     else:
#         await ctx.send(str(ctx.author.name) + "is not in a channel.")

# @bot.command()
# async def queue(ctx:commands.Context, *songs:str):
#     if all([os.path.isfile(f"songs/{song}.mp3") for song in songs]):
#         await ctx.send(f"***Added `{'`, `'.join(songs)}` to queue***")
#         if ctx.guild.id not in global_guild_data.keys():
#             global_guild_data[ctx.guild.id] = {"queue":[*songs]}
#         else:
#             global_guild_data[ctx.guild.id]["queue"].extend(songs)
#     else:
#         await ctx.send("***One or more of the songs you specified were not valid songs, please try again***")
    
# @bot.command()
# async def queueall(ctx:commands.Context):
#     songs = [x.removesuffix(".mp3") for x in os.listdir('songs')]
#     await ctx.send(f"***Added `{'`, `'.join(songs)}` to queue***")
#     if ctx.guild.id not in global_guild_data.keys():
#         global_guild_data[ctx.guild.id] = {"queue":[*songs]}
#     else:
#         global_guild_data[ctx.guild.id]["queue"].extend(songs)

# @bot.command()
# async def shuffle(ctx:commands.Context):
#     random.shuffle(global_guild_data[ctx.guild.id]["queue"])
#     await ctx.send(f"***The Queue has been shuffled***")

# @bot.command(help="A music help command")
# async def music(ctx:commands.Context, arg1:str = None, *arg2:str):
#     if not arg1 and len(arg2) == 0:
#         if ctx.guild.id not in global_guild_data.keys():
#             global_guild_data[ctx.guild.id] = {"queue":[]}
#         if len(global_guild_data[ctx.guild.id]) > 0:
#             embed = discord.Embed(title=f"Currently Playing: ***{global_guild_data[ctx.guild.id][0]}***", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
#             await ctx.send(embed=embed)
#         else:
#             embed = discord.Embed(title=f"No Song Currently Playing", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
#             await ctx.send(embed=embed)
    
#     elif arg1 == "help" or arg1 == "commands":
#         embed = discord.Embed(title=f"Music Help", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
#         embed.add_field(name=f"***!music list***", value="Lists all songs available to play.", inline=False)
#         embed.add_field(name=f"***!music queue***", value="Lists all songs in the queue.", inline=False)
#         embed.add_field(name=f"***!music commands***", value="Shows this menu.", inline=False)
#         embed.add_field(name=f"***!music help***", value="Shows this menu.", inline=False)
#         embed.add_field(name=f"***!play song_name***", value="Plays all music with the provided song at the front of the queue.", inline=False)
#         embed.add_field(name=f"***!play***", value="Plays all music in queue.", inline=False)
#         embed.add_field(name=f"***!queue song_name1 song_name2...***", value="Adds music to the end of the queue.", inline=False)
#         embed.add_field(name=f"***!upload song_name1 song_name2...***", value="Adds attached mp3 file(s) to the bot's filesystem using the name(s) provided as arguments.", inline=False)
#         embed.add_field(name=f"***!queueall***", value="Adds all music to the end of the queue.", inline=False)
#         embed.add_field(name=f"***!shuffle***", value="Shuffles all songs in the queue.", inline=False)
#         await ctx.send(embed=embed)

#     elif arg1 == "list":
#         songs = [x.removesuffix(".mp3") for x in os.listdir('songs')]
#         embed = discord.Embed(title=f"Song List", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
#         for sn, song in enumerate(songs):
#             embed.add_field(name=f"{sn + 1} - *{song}*", value="", inline=False)
#         await ctx.send(embed=embed)
    
#     elif arg1 == "queue":
#         songs = []
#         if ctx.guild.id in global_guild_data.keys():
#             songs = global_guild_data[ctx.guild.id]["queue"]
#         embed = discord.Embed(title=f"Song Queue", description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
#         for sn, song in enumerate(songs):
#             embed.add_field(name=f"{sn+1} - *{song}*", value="", inline=False)
#         await ctx.send(embed=embed)

# @bot.command(help="Uploads the attached song(s) with the name(s) if provided as arguments")
# @commands.has_permissions(administrator=True)
# async def upload(ctx:commands.Context, *args:str):
#     if len(ctx.message.attachments) == 0:
#         await ctx.send("***No songs were attached***")
#         return
#     if not all([attachment.filename.endswith(".mp3") for attachment in ctx.message.attachments]):
#         await ctx.send("***One or more of your songs is not an mp3 file.***")
#         return
    
#     # upload files
#     files = []
#     for an, attachment in enumerate(ctx.message.attachments):
#         song = ""
#         if len(args) > an:
#             file = open(f"songs/{args[an]}.mp3", "wb")
#             file.write(await attachment.read())
#             file.close()
#             song = args[an]
#         else:
#             file = open(f"songs/{attachment.filename.removesuffix('.mp3')}.mp3", "wb")
#             file.write(await attachment.read())
#             file.close()
#             song = attachment.filename.removesuffix('.mp3')
#         files.append(song)
#     embed = discord.Embed(title=f"Added Song{'s' if len(files) > 1 else ''}", description="*For more commands use `!music commands`*", color=16711801)
#     for tn, track in enumerate(files):
#         embed.add_field(name=f"{tn + 1} - *{track}*", value="", inline=False)
#     await ctx.send(embed=embed)


# #ADMINISTRATION
# @bot.command()
# @commands.has_permissions(kick_members=True, ban_members=True, manage_roles=True) # Setting permissions that a user should have to execute this command.
# async def ban(ctx:commands.Context, member: discord.Member, *, reason=None):
#     if member.guild_permissions.administrator: # To check if the member we are trying to mute is an admin or not.
#         await ctx.send(f'Hi {ctx.author.name}! The member you aer trying to mute is a server Administrator. Please don\'t try this on them else they can get angry! :person_shrugging:')

#     else:
#         if reason is None: # If the moderator did not enter any reason.
#             # This command sends DM to the user about the BAN!
#             await member.send(f'Hi {member.name}! You have been banned from {ctx.channel.guild.name}. You must have done something wrong. VERY BAD! :angry: :triumph: \n \nReason: Not Specified')
#             # This command sends message in the channel for confirming BAN!
#             await ctx.send(f'Hi {ctx.author.name}! {member.name} has been banner succesfully from this server! \n \nReason: Not Specified')
#             await member.ban() # Bans the member.
        
#         else: # If the moderator entered a reason.
#             # This command sends DM to the user about the BAN!
#             await member.send(f'Hi {member.name}! You have been banned from {ctx.channel.guild.name}. You must have done something wrong. VERY BAD! :angry: :triumph: \n \nReason: {reason}')
#             # This command sends message in the channel for confirming BAN!
#             await ctx.send(f'Hi {ctx.author.name}! {member.name} has been banner succesfully from this server! \n \nReason: {reason}')
#             await member.ban() # Bans the member.

# #ROLES AND UTILITIES
# @bot.command()
# async def roleprompt(ctx:commands.Context, title:str, *, desc_and_fields:str):
#     df_split = desc_and_fields.splitlines()
#     desc = df_split[0]
#     df_split.pop(0)
#     it = iter(df_split)
#     raw_fields = [*zip(it, it)]
#     embed = discord.Embed(title=title, description="To queue a song use `!queue song_name`\n*For more commands use `!music commands`*", color=16711801)
#     emoji_role_pairs:list[tuple[str, str]] = []
#     for raw_raw_name, raw_value in raw_fields:
#         raw_emoji, raw_name = raw_raw_name.split("$$$")
#         emoji = raw_emoji.strip()
#         role = raw_name.strip()
#         value = raw_value.strip()
#         embed.add_field(name=f"{emoji} - {role}", value=value, inline=False)
#         emoji_role_pairs.append((emoji, role))

#     msg = await ctx.send(embed=embed)
#     for r_emoji, r_role in emoji_role_pairs:
#         await msg.add_reaction(r_emoji)
    
#     if ctx.guild.id in global_guild_data.keys():
#         global_guild_data[ctx.guild.id]["role_msgs"].append({"channelid":ctx.channel.id, "messageid":msg.id, "roles":emoji_role_pairs})
#     else:
#         global_guild_data[ctx.guild.id] = {
#                 "queue":[],
#                 "role_msgs":[
#                     {
#                         "channelid":ctx.channel.id,
#                         "messageid":msg.id,
#                         "roles":emoji_role_pairs
#                     }
#                 ]
#             }

# @bot.event
# async def on_reaction_add(reaction:discord.Reaction, user:discord.Member | discord.User):
#     user_guild = global_guild_data[user.guild.id]
#     Channel = reaction.message.channel
#     if reaction.message.channel.id != Channel.id:
#         return
#     if reaction.emoji == "🏃":
#       Role = discord.utils.get(user.server.roles, name="YOUR_ROLE_NAME_HERE")
#       await user.add_roles(Role)

# bot.run(os.getenv("DISCORD_TOKEN"))