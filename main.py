# Source: https://www.testdevlab.com/blog/how-to-build-a-discord-bot-using-python
import discord
import os
import random
import requests
from discord.ext import commands
from dotenv import load_dotenv
from discord.ui import View, Button, Modal, TextInput

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)
active_games = {}

pre_game_messages = [
    "Get ready to guess!",
    "Let's see if you can guess the number!",
    "The guessing game is about to begin!"
]


class StartGameView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start_button(self, interaction: discord.Interaction, button: Button):
        if self.ctx.author.id in active_games:
            await interaction.response.send_message(
                "You already have an active game! Finish it before starting a new one.", ephemeral=True)
            return
        modal = RangeInputModal(self.ctx)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(selfself, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Game setup canceled.", ephemeral=True)

class RangeInputModal(Modal):
    def __init__(self, ctx):
        super().__init__(title="Set Game Range")
        self.ctx = ctx
        self.range_input = TextInput(label="Enter the maximum range", placeholder="e.g., 100")
        self.add_item(self.range_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_range = int(self.range_input.value)
            if max_range < 1:
                await interaction.response.send_message("Please enter a number greater than 1.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
            return

        secret_number = random.randint(1, max_range)
        active_games[self.ctx.author.id] = {
            "secret_number": secret_number,
            "attempts": 0
        }
        await interaction.response.send_message(f"Game started! I'm thinking of a number between 1 and {max_range}. Start guessing with `/guess <your number>`.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} with ID {bot.user.id}')

@bot.command(name="startGuess")
async def start_guess_ui(ctx):
    pre_game_message = random.choice(pre_game_messages)
    await ctx.send(pre_game_message)

    view = StartGameView(ctx)
    await ctx.send("Ready to start the game?", view=view)

# @bot.command(name="startGuess")
# async def start_guess(ctx, max_range: int):
#     if ctx.author.id in active_games:
#         await ctx.send("You already have an active game! Finish it before starting a new one.")
#         return
#
#     if max_range < 1:
#         await ctx.send("Please enter a positive number greater than 1.")
#         return
#
#     secret_number = random.randint(1, max_range)
#     active_games[ctx.author.id] = {
#         "secret_number": secret_number,
#         "attempts": 0
#     }
#     await ctx.send(f"Game started! I'm thinking of a number between 1 and {max_range}. Start guessing with `/guess <your number>`.")

@bot.command(name="guess")
async def guess(ctx, user_guess: int):
    game = active_games.get(ctx.author.id)

    if game:
        game["attempts"] += 1
        secret_number = game["secret_number"]

        if user_guess < secret_number:
            await ctx.send(f"{ctx.author.mention}, your guess is too low. Try again!")
        elif user_guess > secret_number:
            await ctx.send(f"{ctx.author.mention}, your guess is too high. Try again!")
        else:
            attempts = game["attempts"]
            response = requests.get(f"http://numbersapi.com/{secret_number}")
            trivia = response.text if response.status_code == 200 else "No trivia available."

            await ctx.send(f"🎉 Congrats, {ctx.author.mention}! You guessed the number {secret_number} in {attempts} tries! Fun fact: {trivia}")
            del active_games[ctx.author.id]
    else:
        await ctx.send(f"{ctx.author.mention}, you haven't started a game yet! Type `/startGuess` to begin.")

bot.run(TOKEN)