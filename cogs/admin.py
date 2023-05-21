from discord.ext import commands
import discord
from discord.utils import get as server_get

class Admin(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def purge(self, ctx:commands.Context, number:int|str = 1):
        if number == "all":
            deleted = await ctx.channel.purge()
            await ctx.send(f'Deleted *{len(deleted)}* message{"s" if len(deleted) > 1 else ""}', delete_after=5)
            return
        number = int(number)
        deleted = await ctx.channel.purge(limit=number)
        await ctx.send(f'Deleted *{len(deleted)}* message{"s" if len(deleted) > 1 else ""}', delete_after=5)

    @commands.command()
    @commands.has_permissions(kick_members=True, ban_members=True, manage_roles=True) # Setting permissions that a user should have to execute this command.
    async def ban(self, ctx:commands.Context, member: discord.Member, *, reason=None):
        if member.guild_permissions.administrator: # To check if the member we are trying to mute is an admin or not.
            await ctx.send(f'Hi {ctx.author.name}! The member you aer trying to mute is a server Administrator. Please don\'t try this on them else they can get angry! :person_shrugging:')

        else:
            if reason is None: # If the moderator did not enter any reason.
                # This command sends DM to the user about the BAN!
                await member.send(f'Hi {member.name}! You have been banned from {ctx.channel.guild.name}. You must have done something wrong. VERY BAD! :angry: :triumph: \n \nReason: Not Specified')
                # This command sends message in the channel for confirming BAN!
                await ctx.send(f'Hi {ctx.author.name}! {member.name} has been banner succesfully from this server! \n \nReason: Not Specified')
                await member.ban() # Bans the member.
            
            else: # If the moderator entered a reason.
                # This command sends DM to the user about the BAN!
                await member.send(f'Hi {member.name}! You have been banned from {ctx.channel.guild.name}. You must have done something wrong. VERY BAD! :angry: :triumph: \n \nReason: {reason}')
                # This command sends message in the channel for confirming BAN!
                await ctx.send(f'Hi {ctx.author.name}! {member.name} has been banner succesfully from this server! \n \nReason: {reason}')
                await member.ban() # Bans the member.

async def setup(client):
    await client.add_cog(Admin(client))