from discord.ext import commands
import discord
from discord.utils import get as server_get
from BotClass import DBBot
from discord import app_commands


class Utility(commands.Cog):
    def __init__(self, bot:DBBot):
        self.bot = bot
        self.db = bot.db

    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        if before.channel == None and after.channel != None:
            #joins
            if after.channel.name == "Create A Voice Channel":
                vc_category = server_get(member.guild.categories, name="Voice Channels")
                vc = await member.guild.create_voice_channel(f"Voice - {len(member.guild.voice_channels) - 1}", category=vc_category)
                await member.move_to(vc)
        elif before.channel != None and after.channel == None:
            #leaves
            if before.channel.name != "Create A Voice Channel" and before.channel.category.name == "Voice Channels":
                if len(before.channel.members) <= 0:
                    await before.channel.delete()
        elif before.channel != None and after.channel != None:
            #switches channels
            if before.channel.name != "Create A Voice Channel" and before.channel.category.name == "Voice Channels":
                if len(before.channel.members) <= 0:
                    await before.channel.delete()
            if after.channel.name == "Create A Voice Channel":
                vc_category = server_get(member.guild.categories, name="Voice Channels")
                vc = await member.guild.create_voice_channel(f"Voice - {len(member.guild.voice_channels) - 1}", category=vc_category)
                await member.move_to(vc)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.bot.user}')

    

    @app_commands.command(name="resize")
    async def resize(self, interaction:discord.Interaction, people:app_commands.Range[int, 2, 1000]):
        vc = interaction.user.voice.channel
        if vc:
            await vc.edit(user_limit=int(people))
            await interaction.response.send_message(f"Resizing ***{vc.name}*** to *{people}*")
        else:
            await interaction.response.send_message("You do not appear to be in a voice channel.")

async def setup(client):
    await client.add_cog(Utility(client))