import discord
from discord.ext import commands
from discord.ext.commands import bot
from discord.ui import *
from discord import app_commands

workouts = [
    {
        "user_id": 689438331783872558,
        "sport": "swim",
        "title": "ébresztő",
        "distance": 1200,
        "duration": "00:47:23",
        "description": "hát + gyors piramis (uszony)",
        "rpe": 6
    },
    {
        "user_id": 689438331783872558,
        "sport": "bike",
        "title": "interval",
        "distance": 35.17,
        "duration": "01:20:54",
        "description": "közös SZKSC",
        "rpe": 8
    },
    {
        "user_id": 689438331783872558,
        "sport": "run",
        "title": "pénteki hosszú beszélgetős",
        "distance": 17.45,
        "duration": "01:58:05",
        "description": "+ sütizés",
        "rpe": 5
    },
    {
        "user_id": 689438331783872558,
        "sport": "run",
        "title": "tempo keddi",
        "distance": 6.73,
        "duration": "00:37:42",
        "description": "huh... ez kemény volt",
        "rpe": 7
    }
]

class GetActivitiesView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    def build_embed(self, sport: str, button_style: discord.ButtonStyle):
        color_mapping = {
            discord.ButtonStyle.grey: discord.Color.light_grey(),
            discord.ButtonStyle.blurple: discord.Color.blurple(),
            discord.ButtonStyle.green: discord.Color.green(),
            discord.ButtonStyle.red: discord.Color.red()
        }

        embed = discord.Embed(
            title=f"Here are your {sport} workouts:",
            description=f"**{sport}** workouts",
            color=color_mapping[button_style]
        )
        for i in range(0, len(workouts)):
            if workouts[i]["sport"] == sport or sport == "all":
                workout = workouts[i]
                embed.add_field(
                    name=f"{workout['title']} {'(' + workout['sport'] + ')' if sport == 'all' else ''}",
                    value=f"{workout['distance']}{'m' if workout['sport'] == 'swim' else 'km'}, "
                          f"{workout['duration']}, RPE: {workout['rpe']}, \n\"{workout['description']}\"",
                    inline=False
                )
        embed.set_footer(text="Great job so far. Keep it up!")
        return embed

    @discord.ui.button(label="all", style=discord.ButtonStyle.grey)
    async def all_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(embed=self.build_embed("all", button.style))

    @discord.ui.button(label="swim", style=discord.ButtonStyle.blurple)
    async def swim_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(embed=self.build_embed("swim", button.style))

    @discord.ui.button(label="bike", style=discord.ButtonStyle.green)
    async def bike_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(embed=self.build_embed("bike", button.style))

    @discord.ui.button(label="run", style=discord.ButtonStyle.red)
    async def run_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(embed=self.build_embed("run", button.style))

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="activities", description="shows activities")
    async def activities(self, interaction: discord.Interaction):
        view = GetActivitiesView(interaction.context)
        await interaction.response.send_message("What activities do you want?", view=view)

async def setup(bot):
    await bot.add_cog(Activities(bot))