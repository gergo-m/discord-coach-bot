from datetime import datetime, timedelta, date

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from database import get_activities
from models import Sport
from utils import SPORT_EMOJI, format_duration


def get_week_range(year, week):
    start = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w").date()
    end = start + timedelta(days=6)
    return start, end

def get_month_range(year, month):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end

class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="weekly", description="Show your weekly activity summary")
    @app_commands.describe(week="ISO week number (1-53), defaults to current week", sport="Filter by specific sport, defaults to all")
    @app_commands.choices(
        sport=[
            app_commands.Choice(name=sport.value, value=sport.value) for sport in Sport
        ]
    )
    async def weekly(self, interaction: Interaction, week: int = None, sport: str = "all"):
        today = datetime.now().date()
        year = today.year
        week = week or today.isocalendar()[1]
        sport_enum = Sport(sport.lower())
        start, end = get_week_range(year, week)

        activities = get_activities(interaction.user.id, sport_enum if sport_enum != Sport.ALL else None)
        activities = [a for a in activities if start <= a.date <= end]

        if not activities:
            await interaction.response.send_message(f"No activities found for week {week}, {sport_enum.value}.",
                                                    ephemeral=True)
            return

        total_distance = sum(a.distance for a in activities)
        total_elevation = sum(a.elevation for a in activities)
        total_duration = sum((a.duration for a in activities), timedelta())

        embed = discord.Embed(
            title=f"Weekly Summary (Week {week}, {start} - {end}) [{sport_enum.value.capitalize()}]",
            description=f"Activities: {len(activities)}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Total Distance", value=f"{total_distance:.2f} km",
            inline=True
        )
        if sport_enum != Sport.SWIM:
            embed.add_field(
                name="Total Elevation", value=f"{total_elevation} m",
                inline=True
            )
        embed.add_field(
            name="Total Duration", value=f"{format_duration(total_duration)}",
            inline=True
        )

        activity_list = "\n".join(f"- {SPORT_EMOJI[a.sport]} {a.title} ({a.date})" for a in activities[:10])
        embed.add_field(name="Great job in activities like...", value=activity_list, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="monthly", description="Show your monthly activity summary")
    @app_commands.describe(month="Month number (1-12), defaults to current month", sport="Filter by specific sport, defaults to all")
    @app_commands.choices(
        sport=[
            app_commands.Choice(name=sport.value, value=sport.value) for sport in Sport
        ]
    )
    async def monthly(self, interaction: Interaction, month: int = None, sport: str = "all"):
        today = datetime.now().date()
        year = today.year
        month = month or today.month
        sport_enum = Sport(sport.lower())
        start, end = get_month_range(year, month)

        activities = get_activities(interaction.user.id, sport_enum if sport_enum != Sport.ALL else None)
        activities = [a for a in activities if start <= a.date <= end]

        if not activities:
            await interaction.response.send_message(
                f"No activities found for {start.strftime('%B %Y')}, {sport_enum.value}.", ephemeral=True)
            return

        total_distance = sum(a.distance for a in activities)
        total_elevation = sum(a.elevation for a in activities)
        total_duration = sum((a.duration for a in activities), timedelta())

        embed = discord.Embed(
            title=f"Monthly Summary ({start.strftime('%B %Y')}) [{sport_enum.value.capitalize()}]",
            description=f"Activities: {len(activities)}",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Distance", value=f"{total_distance:.2f} km", inline=True)
        embed.add_field(name="Total Elevation", value=f"{total_elevation} m", inline=True)
        embed.add_field(name="Total Duration", value=f"{format_duration(total_duration)}", inline=True)

        activity_list = "\n".join(f"- {SPORT_EMOJI[a.sport]} {a.title} ({a.date})" for a in activities[:10])
        embed.add_field(name="Great job in activities like...", value=activity_list, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reports(bot))