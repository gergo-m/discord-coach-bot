import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import app_commands
from database import get_activities
from models import Sport, SportEmoji
from utils import format_distance, start_time_to_string, date_to_string, get_type_with_sport, format_duration, \
    SPORT_EMOJI, format_pace_speed


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

        activities = get_activities(user_id, sport if sport != Sport.ALL else None)

        embed = discord.Embed(
            title=f"📊 {sport.value.capitalize() if sport != Sport.ALL else 'All'} Activities",
            color=color_mapping[button_style]
        )
        for activity in activities:
            value_lines = [
                f"**Date:** {date_to_string(activity.date)} at {start_time_to_string(activity.start_time)}",
                f"**Type:** {get_type_with_sport(activity.activity_type, activity.sport, True)}",
                f"**Distance:** {format_distance(activity.distance, activity.sport)}",
                f"**Duration:** {format_duration(activity.duration)}",
                f"{format_pace_speed(activity)}"
            ]

            if activity.elevation_gain > 0:
                value_lines.append(f"**Elevation Gain:** {activity.elevation_gain}m")

            if activity.avg_heart_rate > 0:
                value_lines.append(f"**Avg HR:** {activity.avg_heart_rate} bpm")

            if activity.max_heart_rate > 0:
                value_lines.append(f"**Max HR:** {activity.max_heart_rate} bpm")

            value_lines.append(f"**RPE:** {activity.rpe}/10\n---")

            if activity.location:
                value_lines.append(f"**Location:** {activity.location}")

            if activity.weather:
                value_lines.append(f"**Weather:** {activity.weather}")

            if activity.feelings:
                value_lines.append(f"**Feelings:** {activity.feelings}")

            if activity.description:
                value_lines.append(f"**Description:**\n{activity.description}\n---")

            equipment_str = ", ".join([f"{eq.name} ({eq.type.value})" for eq in activity.equipment_used]) or "None"
            if equipment_str != "None":
                value_lines.append(f"🔧 **Equipment:** {equipment_str}\n---")

            embed.add_field(
                name=f"{SPORT_EMOJI[activity.sport]} {activity.title}",
                value="\n".join(value_lines) + "------------",
                inline=True
            )

        if not activities:
            embed.description = f"No activities found. Time to get moving! {SportEmoji.SWIM.value}{SportEmoji.BIKE.value}{SportEmoji.RUN.value}"
        else:
            embed.set_footer(text="Great job so far. Keep it up! 💪")
        return embed

    @discord.ui.button(label=Sport.ALL.value.capitalize(), style=discord.ButtonStyle.grey, emoji=SportEmoji.ALL.value)
    async def all_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.ALL, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label=Sport.SWIM.value.capitalize(), style=discord.ButtonStyle.blurple, emoji=SportEmoji.SWIM.value)
    async def swim_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.SWIM, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label=Sport.BIKE.value.capitalize(), style=discord.ButtonStyle.green, emoji=SportEmoji.BIKE.value)
    async def bike_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.BIKE, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label=Sport.RUN.value.capitalize(), style=discord.ButtonStyle.red, emoji=SportEmoji.RUN.value)
    async def run_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_embed(interaction.user.id, Sport.RUN, button.style)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="activities", description="View your logged activities")
    async def activities(self, interaction: discord.Interaction):
        view = GetActivitiesView(interaction.context)
        await interaction.response.send_message(
            "Choose activity type to view:",
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Activities(bot))
