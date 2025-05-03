# Source: https://www.testdevlab.com/blog/how-to-build-a-discord-bot-using-python
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from database import init_db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

init_db()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} with ID {bot.user.id}')
    GUILD_ID = 1361987311008485466
    guild = await bot.fetch_guild(GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)


# Source: https://stackoverflow.com/questions/66662756/is-it-possible-to-split-a-discord-py-bot-across-multiple-files
async def load():
    await bot.load_extension('cogs.guessing_game')
    await bot.load_extension('cogs.add_activity')
    await bot.load_extension('cogs.delete_activity')
    await bot.load_extension('cogs.activities')
    await bot.load_extension('cogs.add_equipment')
    await bot.load_extension('cogs.delete_equipment')
    await bot.load_extension('cogs.retire_equipment')
    await bot.load_extension('cogs.unretire_equipment')
    await bot.load_extension('cogs.equipment')
    await bot.load_extension('cogs.quickadd')
    await bot.load_extension('cogs.reports')
    await bot.load_extension('cogs.leaderboards')
    await bot.load_extension('cogs.strava')

if __name__ == '__main__':
    import asyncio
    asyncio.run(load())
    bot.run(TOKEN)