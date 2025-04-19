from typing import Any

import discord
from discord import app_commands, Interaction
from discord._types import ClientT
from discord.ext import commands
from datetime import datetime

from discord.ui import Button

from database import get_activities, delete_activity
from models import Sport
from utils import start_time_to_string, format_distance

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, activity_id):
        super().__init__(timeout=30)
        self.activity_id = activity_id

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.grey)
    async def confirm(self, interaction, button):
        delete_activity(self.activity_id)
        await interaction.response.edit_message(
            content="✅ Activity deleted.",
            view=None
        )
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="❌ Deletion cancelled.", view=None)
        self.stop()

class DeleteActivitySelect(discord.ui.Select):
    def __init__(self, activities):
        options = []
        for activity in activities:
            start_time = start_time_to_string(activity.start_time)
            label = f"{activity.title} ({start_time})"
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(activity.id),
                    description=f"{activity.sport.value.capitalize()} - {format_distance(activity.distance, activity.sport)}"
                )
            )
        super().__init__(
            placeholder="Select an activity to delete...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        activity_id = int(self.values[0])
        await interaction.response.send_message(
            content="Are you sure you want to delete this activity?",
            view=ConfirmDeleteView(activity_id)
        )

class DeleteActivityView(discord.ui.View):
    def __init__(self, activities):
        super().__init__(timeout=30)
        self.add_item(DeleteActivitySelect(activities))


class DeleteActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="deleteactivity", description="Delete one of your activities")
    async def deleteactivity(self, interaction: Interaction):
        activities = get_activities(interaction.user.id)

        if not activities:
            await interaction.response.send_message(
                "You have no activities to delete!",
                ephemeral=True
            )
            return

        view = DeleteActivityView(activities)
        await interaction.response.send_message(
            "Which activity would you like to delete?",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(DeleteActivity(bot))