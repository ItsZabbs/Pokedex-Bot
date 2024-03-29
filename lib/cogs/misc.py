from typing import Optional, Union
import discord
from discord import app_commands
from discord.ext import commands
from time import time
from discord.ext import tasks
from discord.ext.commands.cooldowns import BucketType
from discord.ext.commands import command,Context,hybrid_command
from random import choice


from ..db import db
from ..bot import Bot

memes=['SPOILER_3.gif', 'SPOILER_1.jpg', 'SPOILER_2.gif']

def check_meme_server(ctx:Context):
    return ctx.guild is not None and ctx.guild.id==857700650992795648
class Misc(commands.Cog):
    '''Miscellaneous commands'''
    url="miscellaneous"
    def __init__(self, bot:Bot):
        self.bot = bot
        self.presence_update.start()
    def cog_unload(self):
        self.presence_update.cancel()
        return super().cog_unload()
    @hybrid_command(name='invite',help='Provides an invite link for the bot',extras={"url":"invite"})
    async def sendinvite(self,ctx):
        embed = discord.Embed(title=f'Add {self.bot.user} to your server!',colour=ctx.author.colour,description=f"Click **[here](https://discord.com/oauth2/authorize?client_id=853556227610116116&permissions=277092812864&scope=bot%20applications.commands)** to invite the bot to your server!")
        await ctx.send(embed=embed)
    @command(name='killtab')
    @commands.check(check_meme_server)
    async def killtab(self,ctx):
        # embed=discord.Embed(colour=ctx.author.colour)
        # embed.set_image(url="https://cdn.discordapp.com/attachments/752901803124719639/"+choice(memes))
        await ctx.send(file=discord.File("data/images/"+choice(memes),spoiler=True))
    @commands.group(extras={"url":"prefix-management"})
    @commands.guild_only()
    async def prefix(self,ctx):
        '''Prefix commands to set what the bot responds to'''
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid prefix command passed...')

    @prefix.command(name="add",help='Adds a prefix , max length is 10 chars',extras={"url":"span-stylecoloryellowhow-to-add-a-prefix-span"})
    @commands.has_permissions(manage_guild=True)
    async def add_prefix(self, ctx, new):
        if len(new) > 10:
            return await ctx.send("The prefix can not be more than 10 characters in length.")
        await db.insert_new_prefix(ctx.guild.id,new)
        prefixes=await db.prefix_cache[ctx.guild.id]
        assert isinstance(prefixes,list)
        embed=discord.Embed(title='All prefixes are:',description="\n".join([f"{i}. `{prefix}`" for i,prefix in enumerate(prefixes,start=1)]))
        await ctx.send(embed=embed)

    @prefix.command(name='remove',extras={"url":"span-stylecoloryellowhow-to-remove-a-prefix-span"})
    @commands.has_permissions(manage_guild=True)
    async def remove_prefix(self,ctx,old:str):
        '''Removes a prefix from the current existing prefixes'''
        await db.remove_prefix(ctx.guild.id,old)
        if not await db.prefix_cache[ctx.guild.id]:
            await db.insert_new_prefix(ctx.guild.id,"dexy")
        prefixes=await db.prefix_cache[ctx.guild.id]
        assert isinstance(prefixes,list)
        embed=discord.Embed(title='All prefixes are:',description="\n".join([f"{i}. `{prefix}`" for i,prefix in enumerate(prefixes,start=1)]))
        await ctx.send(embed=embed)
    @prefix.command(name='list',extras={"url":"span-stylecoloryellowhow-to-list-all-prefixes-span"})
    async def list_prefix(self,ctx):
        '''Lists all the server's prefixes'''
        prefixes=await db.prefix_cache[ctx.guild.id]
        assert isinstance(prefixes,list)
        embed=discord.Embed(title='All prefixes are:',description="\n".join([f"{i}. `{prefix}`" for i,prefix in enumerate(prefixes,start=1)]) or f"It seems like there are no prefixes. Add one using {ctx.prefix} prefix add <prefix>")
        await ctx.send(embed=embed)
    @prefix.error
    async def add_prefix_error(self, ctx, exc):
        if isinstance(exc, commands.CheckFailure):
            await ctx.send("You need the Manage Server permission to do that.")

    @hybrid_command(name='ping',aliases=['latency'],extras={"url":"ping"})
    async def ping_command(self,ctx:Context):
        '''Ping Pong!'''
        start = time()
        if isinstance(ctx.interaction,discord.Interaction):
            await ctx.send(f"Pong! DWSP latency: {self.bot.latency * 1000:,.0f} ms.")
            end=time()
            await ctx.interaction.edit_original_response(content=f"Pong! DWSP latency: {self.bot.latency * 1000:,.0f} ms. Response time: {(end - start) * 1000:,.0f} ms.")
        else:
            message = await ctx.send(f"Pong! DWSP latency: {self.bot.latency * 1000:,.0f} ms.")
            end = time()
            await message.edit(content=f"Pong! DWSP latency: {self.bot.latency * 1000:,.0f} ms. Response time: {(end - start) * 1000:,.0f} ms.")
    @hybrid_command(name='about',aliases=['info'],extras={"url":"about"})
    async def about_command(self,ctx:Context):
        '''Sends information about the bot and its developer'''
        embed=discord.Embed(title="About me",description=f'I was given life by <@!{self.bot.owner_id}> (Zabbs#6530)! \n See `{("@"+ctx.me.name) if ctx.prefix=="/" else "dexy"} help Pokemon` for all my Pokemon utilities!',colour=ctx.me.colour)
        embed.set_author(name=ctx.me.name,icon_url=ctx.me.avatar.url)
        embed.set_footer(text='The Discord bot Beheeyem\'s design for embeds and data presentation has been used')
        await ctx.send(embed=embed)
    @commands.cooldown(1,60.0,BucketType.user)
    @hybrid_command(name='feedback',aliases=['feed','back'],extras={"url":"feedback"})
    @app_commands.describe(feedback="The feedback you want to send!",private="If you want others to see your feedback")
    async def feedback(self,ctx:Context|discord.Interaction,*,feedback,private:bool=True):
        '''Any kind of feedback or questions are accepted. Even any concerns regarding the bot.'''
        if len(feedback)>1024:
            return await ctx.send("Please limit your feedback to 1024 characters or less")
        embed=discord.Embed(title=f'Feedback from user {ctx.author.name}#{ctx.author.discriminator}')
        embed.add_field(name='User ID',value=ctx.author.id,inline=False)
        embed.add_field(name='Feedback',value=feedback,inline=False)
        await self.bot.feedback_webhook.send(embed=embed)
        if isinstance(ctx.interaction,discord.Interaction):
            await ctx.send("Feedback sent!",ephemeral=private if private is not None else False)
        else:
            await ctx.message.add_reaction('✅')
    
    # @commands.hybrid_command(name='vote',aliases=['support'],extras={"url":"vote"})
    # async def vote(self,ctx):
    #     """Support the bot!"""
    #     embed=discord.Embed(title="Support the bot and it's developer!",description='Donate [here](https://buymeacoffee.com/Zabbs)\nUpvote the bot on [top.gg](https://top.gg/bot/853556227610116116) or [botlist](https://discordbotlist.com/bots/pokedex-bot)')
    #     return await ctx.send(embed=embed)
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{Misc.__qualname__} up")

    @tasks.loop(minutes=5.0)
    async def presence_update(self):
        assert self.bot.user is not None
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"for @{self.bot.user.name} "+('help!' if self.presence_update.current_loop%2 else 'invite!')))
    @presence_update.before_loop
    async def before_presence(self):
        print('waiting to update presence until ready...')
        await self.bot.wait_until_ready()
    # @hybrid_command(name='command_stats')
    # async def cmd_stats(self,ctx)
async def setup(bot):
    await bot.add_cog(Misc(bot))


