import discord
from discord.ext import commands

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        """Says hello"""
        await ctx.send(f'Hello')
        
        
async def setup(bot):
    await bot.add_cog(Testing(bot))