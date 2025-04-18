import discord
from discord.ext import commands
from discord.ext.commands import bot
from discord.ui import View, Button
from discord import app_commands, Interaction

from database import get_activities, delete_activity
from models import Sport, Activity
from utils import format_distance, start_time_to_string

class GetActivitiesView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    def build_embed(self, user_id, sport: Sport, button_style: discord.ButtonStyle):
        color_mapping = {
            discord.ButtonStyle.grey: discord.Color.light_grey(),
            discord.ButtonStyle.blurple: discord.Color.blurple(),
            discord.ButtonStyle.green: discord.Color.green(),
            discord.ButtonStyle.red: discord.Color.red()
        }

        if sport is not Sport.ALL:
            activities = get_activities(user_id, sport)
        else:
            activities = get_activities(user_id)

        print(activities)

        embed = discord.Embed(
            title=f"Here are your {sport.value} activities:",
            description=f"**{sport.value.capitalize()}** activities",
            color=color_mapping[button_style]
        )
        for activity in activities:
            if activity.sport == sport or sport == Sport.ALL:
                distance_str = format_distance(activity.distance, sport)
                embed.add_field(
                    name=f"{activity.title} {'(' + activity.sport.value + ')' if sport == Sport.ALL else ''} at {start_time_to_string(activity.start_time)}",
                    value=f"{distance_str}, {activity.duration}, RPE: {activity.rpe}, \n\"{activity.description}\"",
                    inline=False
                )
        embed.set_footer(text="Great job so far. Keep it up!")
        return embed

    @discord.ui.button(label=Sport.ALL.value, style=discord.ButtonStyle.grey)
    async def all_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.ALL, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label=Sport.SWIM.value, style=discord.ButtonStyle.blurple)
    async def swim_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.SWIM, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label=Sport.BIKE.value, style=discord.ButtonStyle.green)
    async def bike_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.BIKE, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label=Sport.RUN.value, style=discord.ButtonStyle.red)
    async def run_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.RUN, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="activities", description="shows activities")
    async def activities(self, interaction: discord.Interaction):
        view = GetActivitiesView(interaction.context)
        await interaction.response.send_message("What activities do you want?", view=view)

async def setup(bot):
    await bot.add_cog(Activities(bot))