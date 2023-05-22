from discord.ext import commands
import discord
from discord.utils import get as server_get
from BotClass import DBBot
from utility import rgbtoint32

class Admin(commands.Cog):
    def __init__(self, bot:DBBot):
        self.bot = bot
        self.db = bot.db

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

    @commands.Cog.listener()
    async def on_guild_remove(self, guild:discord.Guild):
        await self.db.guild.delete_many({"gid":guild.id})
        await self.db.queue.delete_many({"gid":guild.id})
        await self.db.role_messages.delete_many({"gid":guild.id})

    @commands.command(help="THIS IS MAINLY A DEVELOPMENT COMMAND AND SHOULD ONLY BE USED IF THE BOT FAILED TO CONFIGURE THE SERVER WHEN JOINING THE SERVER.")
    @commands.has_permissions(administrator=True)
    async def CONFIGURE(self, ctx:commands.Context):
        await ctx.send("***WARNING: THIS IS MAINLY A DEVELOPMENT COMMAND AND SHOULD ONLY BE USED IF THE BOT FAILED TO CONFIGURE THE SERVER WHEN JOINING THE SERVER.***")
        await ctx.send("***Configuring...***")
        await self.on_guild_join(ctx.guild)
        await ctx.send("***Configuration Complete!***")

    
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

    #START ROLES

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def roleprompt(self, ctx:commands.Context, red:int, green:int, blue:int, *, desc_and_fields:str):
        df_split = desc_and_fields.splitlines()
        title = df_split[0]
        df_split.pop(0)
        desc = df_split[0]
        df_split.pop(0)
        it = iter(df_split)
        raw_fields = [*zip(it, it)]
        embed = discord.Embed(title=title, description=desc, color=rgbtoint32([red,green,blue]))
        emoji_role_pairs:list[list[str, str]] = []
        for raw_raw_name, raw_value in raw_fields:
            raw_emoji, raw_name = raw_raw_name.split("$$$")
            emoji = raw_emoji.strip()
            role = raw_name.strip()
            value = raw_value.strip()
            embed.add_field(name=f"{emoji} - {role}", value=value, inline=False)
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
            if str(reaction.emoji) == str(rolereaction):
                Role = discord.utils.get(reaction.member.guild.roles, name=role)
                await reaction.member.add_roles(Role)
                valid_reaction = True

        if not valid_reaction:
            guild = self.bot.get_guild(reaction.guild_id)
            channel = guild.get_channel(reaction.channel_id)
            message = await channel.fetch_message(reaction.message_id)
            await message.remove_reaction(reaction.emoji, reaction.member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction:discord.RawReactionActionEvent):
        guild = self.bot.get_guild(reaction.guild_id)
        role_msg = await self.db.role_messages.find_one({
            "gid":reaction.guild_id,
            "channelid":reaction.channel_id,
            "messageid":reaction.message_id
        })

        # Return if the message is not in the db
        if role_msg == None:
            return
        
        for rolereaction, role in role_msg["roles"]:
            #print(f"{str(reaction.emoji) == str(rolereaction)}")
            if str(reaction.emoji) == str(rolereaction):
                Role:discord.Role = discord.utils.get(guild.roles, name=role)
                user:discord.Member = await guild.fetch_member(reaction.user_id)
                await user.remove_roles(Role)


    @commands.Cog.listener()
    async def on_raw_message_delete(self, message:discord.RawMessageDeleteEvent):
        role_msg = await self.db.role_messages.find_one({
            "gid":message.guild_id,
            "channelid":message.channel_id,
            "messageid":message.message_id
        })
        if role_msg != None:
            await self.db.role_messages.delete_one({
                "gid":message.guild_id,
                "channelid":message.channel_id,
                "messageid":message.message_id
            })


    #END ROLES

async def setup(client):
    await client.add_cog(Admin(client))