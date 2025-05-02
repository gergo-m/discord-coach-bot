from datetime import date, timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from database import get_activities
from models import Sport
from utils import format_duration


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_time_range(self, timeframe: str):
        today = date.today()
        if timeframe == "weekly":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
        elif timeframe == "monthly":
            start = date(today.year, today.month, 1)
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        else:
            start = today
            end = today
        return start, end

    async def generate_leaderboard(self, interaction, timeframe: str, sport: str = "all", sort_by: str = "distance"):
        start, end = self.get_time_range(timeframe)
        sport_enum = Sport(sport.lower()) if sport else Sport.ALL

        all_activities = get_activities(
            user_id=None,
            sport=sport_enum if sport_enum != Sport.ALL else None,
            start_date=start,
            end_date=end
        )

        user_stats = {}
        for activity in all_activities:
            user_id = activity.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'distance': 0.0,
                    'duration': timedelta(),
                    'activities': 0,
                    'user': None
                }
            user_stats[user_id]['distance'] += activity.distance
            user_stats[user_id]['duration'] += activity.duration
            user_stats[user_id]['activities'] += 1

        for user_id in user_stats:
            user = await interaction.guild.fetch_member(user_id)
            user_stats[user_id]['user'] = user.display_name if user else f"Unknown User ({user_id})"

        sorted_stats = sorted(
            user_stats.values(),
            key=lambda x: x[sort_by],
            reverse=True
        )[:10]

        embed = discord.Embed(
            title=f"{timeframe.capitalize()} Leaderboard for {sort_by.capitalize()} ({sport_enum.value.capitalize()})",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Period: {start} to {end}")

        for idx, stats in enumerate(sorted_stats, 1):
            embed.add_field(
                name=f"{idx}. {stats['user']}",
                value=(
                    f"Distance: {self.make_bold('distance', sort_by)}{stats['distance']:.1f} km{self.make_bold('distance', sort_by)}\n"
                    f"Duration: {self.make_bold('duration', sort_by)}{format_duration(stats['duration'], False)}{self.make_bold('duration', sort_by)}\n"
                    f"Activities: {self.make_bold('activities', sort_by)}{stats['activities']}{self.make_bold('activities', sort_by)}"
                ),
                inline=False
            )

        return embed

    def make_bold(self, stat, sort_by):
        if stat == sort_by:
            return "**"
        else:
            return ""

    @app_commands.command(name="leaderboard", description="Show activity leaderboards")
    @app_commands.describe(
        timeframe="Time period for leaderboard",
        sport="Filter by specific sport, defaults to all",
        sort_by="Sort leaderboard by this metric, defaults to distance"
    )
    @app_commands.choices(
        timeframe=[
            app_commands.Choice(name="weekly", value="weekly"),
            app_commands.Choice(name="monthly", value="monthly")
        ],
        sport=[
            app_commands.Choice(name=sport.value, value=sport.value) for sport in Sport
        ],
        sort_by=[
            app_commands.Choice(name="Distance", value="distance"),
            app_commands.Choice(name="Duration", value="duration"),
            app_commands.Choice(name="Activities", value="activities"),
        ]
    )
    async def leaderboard(self, interaction: discord.Interaction, timeframe: str, sport: str = "all", sort_by: str = "distance"):
        try:
            embed = await self.generate_leaderboard(interaction, timeframe, sport, sort_by)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except Exception as e:
            await interaction.response.send_message(
                f"Error generating leaderboard: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))