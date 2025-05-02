import re
from datetime import datetime, timedelta, time

import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import List

from models import Activity, Sport, ActivityType, EquipmentType, Equipment
from database import add_activity, get_activities, get_equipments
from utils import format_distance, start_time_to_string, start_time_from_string, date_from_string, date_to_string, \
    is_type_appropriate, get_type_with_sport, SPORT_BUTTON_STYLE, SPORT_EMOJI


class AddActivityView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

        for sport in Sport:
            if sport == Sport.ALL:
                continue

            self.add_item(
                Button(
                    label=sport.value.capitalize(),
                    style=SPORT_BUTTON_STYLE[sport],
                    emoji=SPORT_EMOJI[sport],
                    custom_id=f"sport_{sport.value}",
                )
            )

    async def interaction_check(self, interaction: discord.Interaction):
        sport_value = interaction.data["custom_id"].split("_")[1]
        sport = Sport(sport_value)
        modal = CoreInputModal(self.ctx, sport)
        await interaction.response.send_modal(modal)
        return False


class CoreInputModal(Modal):
    def __init__(self, ctx, sport: Sport):
        super().__init__(title=f"🎉 {sport.value.capitalize()} Activity Details (1/3)")
        self.ctx = ctx
        self.sport = sport

        self.date_input = TextInput(
            label="🗓️ Date (yyyy-mm-dd)",
            placeholder="Tip: leave empty for 'today'",
            required=False
        )
        self.start_time_input = TextInput(
            label="🕒 Start time (hh:mm)",
            placeholder="Early riser? 05:07 | After work? 16:47"
        )
        self.title_input = TextInput(
            label="🟢 Title",
            placeholder="Peaceful run on the beach... or self-torture in the rain?",
            max_length=50
        )

        self.add_item(self.date_input)
        self.add_item(self.start_time_input)
        self.add_item(self.title_input)

    async def on_submit(self, interaction: discord.Interaction):
        # validate start_time
        if not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", self.start_time_input.value):
            return await interaction.response.send_message(
                "⏰ Please use `hh:mm` 24-hour format for start time (e.g. 05:07, 16:47)",
                ephemeral=True
            )

        date = date_from_string(self.date_input.value) if self.date_input.value else datetime.now().date()
        start_time = start_time_from_string(self.start_time_input.value)

        # create activity
        activity = Activity(
            user_id=interaction.user.id,
            sport=self.sport,
            date=date,
            start_time=start_time,
            title=self.title_input.value,
        )

        await interaction.response.send_message("Great! Press the button below to add activity data:", view=ContinueToDataView(activity), ephemeral=True)

class ContinueToDataView(View):
    def __init__(self, activity: Activity):
        super().__init__()
        self.activity = activity

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.blurple)
    async def continue_to_data(self, interaction: discord.Interaction, button: Button):
        modal = DataInputModal(self.activity)
        await interaction.response.send_modal(modal)

class DataInputModal(Modal):
    def __init__(self, activity: Activity):
        super().__init__(title=f"🎉 {activity.sport.value.capitalize()} Activity Details (2/3)")
        self.activity = activity

        self.distance_input = TextInput(
            label=f"🛣️ Distance ({'km' if activity.sport != Sport.SWIM else 'meters'})",
            placeholder="Marathon? 42.2 | Sprint? 0.1 | Pool laps? 1500"
        )
        if self.activity.sport != Sport.SWIM:
            self.elevation_gain_input = TextInput(
                label="🗻 Elevation Gain (meters)",
                placeholder="No mountains in sight? 2 | Hilly ride? 625"
            )
        self.duration_input = TextInput(
            label="⏰ Duration (hh:mm:ss)",
            placeholder="Speedy? 00:18:32 | Scenic route? 01:45:23"
        )
        self.avg_heart_rate_input = TextInput(
            label="💗 Average Heart Rate (bpm)",
            placeholder="Calm like a cactus? 85 | Verge of collapse? 181",
            required=False
        )
        self.max_heart_rate_input = TextInput(
            label="💓 Max Heart Rate (bpm)",
            placeholder="Recovering? 113 | Did some sprints? 197",
            required=False
        )

        self.add_item(self.distance_input)
        if self.activity.sport != Sport.SWIM:
            self.add_item(self.elevation_gain_input)
        self.add_item(self.duration_input)
        self.add_item(self.avg_heart_rate_input)
        self.add_item(self.max_heart_rate_input)

    async def on_submit(self, interaction: Interaction):
        # validate duration
        if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$", self.duration_input.value):
            return await interaction.response.send_message(
                "⏰ Whoa time traveler! Use `hh:mm:ss` format for duration (e.g. 01:30:45)",
                ephemeral=True
            )

        # validate distance
        try:
            distance = float(self.distance_input.value)
            if distance <= 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "🛣️ Distance needs to be a positive number!",
                ephemeral=True
            )

        # validate elevation_gain
        if self.activity.sport != Sport.SWIM:
            try:
                elevation_gain = int(self.elevation_gain_input.value)
                if elevation_gain < 0:
                    raise ValueError
            except ValueError:
                return await interaction.response.send_message(
                    "🗻 Elevation Gain needs to be a non-negative number!",
                    ephemeral=True
                )

        # validate avg_heart_rate
        if self.avg_heart_rate_input.value:
            try:
                avg_heart_rate = int(self.avg_heart_rate_input.value)
                if avg_heart_rate <= 0:
                    raise ValueError
            except ValueError:
                return await interaction.response.send_message(
                    "💗 Average Heart Rate needs to be a positive number!",
                    ephemeral=True
                )

        # validate max_heart_rate
        if self.max_heart_rate_input.value:
            try:
                max_heart_rate = int(self.max_heart_rate_input.value)
                if max_heart_rate <= 0:
                    raise ValueError
            except ValueError:
                return await interaction.response.send_message(
                    "💓 Max Heart Rate needs to be a positive number!",
                    ephemeral=True
                )

        h, m, s = map(int, self.duration_input.value.split(":"))
        duration = timedelta(hours=h, minutes=m, seconds=s)

        self.activity.distance = distance
        if self.activity.sport != Sport.SWIM:
            self.activity.elevation_gain = elevation_gain
        self.activity.duration = duration
        if self.avg_heart_rate_input.value:
            self.activity.avg_heart_rate = avg_heart_rate
        if self.max_heart_rate_input.value:
            self.activity.max_heart_rate = max_heart_rate

        await interaction.response.send_message("Almost there! Press the button below to add some final details:",
                                                view=ContinueToDetailsView(self.activity),
                                                ephemeral=True)

class ContinueToDetailsView(View):
    def __init__(self, activity: Activity):
        super().__init__()
        self.activity = activity

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.blurple)
    async def continue_to_details(self, interaction: discord.Interaction, button: Button):
        modal = DetailsInputModal(self.activity)
        await interaction.response.send_modal(modal)

class DetailsInputModal(Modal):
    def __init__(self, activity: Activity):
        super().__init__(title=f"🎉 {activity.sport.value.capitalize()} Activity Details (3/3)")
        self.activity = activity

        self.description_input = TextInput(
            label="💬 Description - Tell me all about it!",
            placeholder="Felt unstoppable? Drowned in sweat?",
            style=discord.TextStyle.long,
            required=False
        )
        self.location_input = TextInput(
            label="🗺️ Location (City, Country)",
            placeholder="e.g. Szeged, Hungary",
            required=False
        )
        self.weather_input = TextInput(
            label="🌦️ Weather (Celsius)",
            placeholder="Cold headwinds? windy 8 | Sweaty? sunny 27",
            required=False
        )
        self.feelings_input = TextInput(
            label="🎭 How did this activity feel?",
            placeholder="Make this as detailed as you'd like.",
            style=discord.TextStyle.long,
            required=False
        )

        self.add_item(self.description_input)
        self.add_item(self.location_input)
        self.add_item(self.weather_input)
        self.add_item(self.feelings_input)

    async def on_submit(self, interaction: Interaction):
        self.activity.description = self.description_input.value
        self.activity.location = self.location_input.value
        self.activity.weather = self.weather_input.value
        self.activity.feelings = self.feelings_input.value

        # RPE selection
        await interaction.response.send_message(
            "What type of activity was this?",
            view=ActivityTypeSelectView(self.activity),
            ephemeral=True
        )


class ActivityTypeSelectView(discord.ui.View):
    def __init__(self, activity: Activity):
        super().__init__(timeout=30)
        self.activity = activity

        options = [
            discord.SelectOption(
                label=get_type_with_sport(atype, self.activity.sport, True),
                value=atype.value,
                description=f"Select for {get_type_with_sport(atype, self.activity.sport, False)} sessions"
            ) for atype in ActivityType if is_type_appropriate(atype, self.activity.sport)
        ]

        self.add_item(discord.ui.Select(
            placeholder="Choose activity type...",
            options=options,
            custom_id="activity_type"
        ))

    async def interaction_check(self, interaction: Interaction):
        selected_type = self.children[0].values[0]
        self.activity.activity_type = ActivityType(selected_type)
        await interaction.response.defer()

        await interaction.followup.send(
            "How hard did this activity feel? (Rate 1-10)",
            view=RPEView(self.activity),
            ephemeral=True
        )
        self.stop()

class RPEView(View):
    def __init__(self, activity: Activity):
        super().__init__(timeout=30)
        self.activity = activity

        for i in range(1, 11):
            style = discord.ButtonStyle.grey
            if i >= 9: style = discord.ButtonStyle.red
            elif i >= 7: style = discord.ButtonStyle.green
            elif i >= 4: style = discord.ButtonStyle.blurple

            self.add_item(
                Button(
                    label=str(i),
                    style=style,
                    custom_id=f"rpe_{i}"
                )
            )

    async def interaction_check(self, interaction: discord.Interaction):
        rpe = int(interaction.data["custom_id"].split("_")[1])
        self.activity.rpe = rpe

        user_equipment = get_equipments(interaction.user.id, self.activity.sport)

        if not user_equipment:
            add_activity(self.activity)
            await self.send_confirmation(interaction)
        else:
            await interaction.response.edit_message(
                content="Select equipment used (optional):",
                view=EquipmentSelectView(self.activity, user_equipment)
            )
        self.stop()

    async def send_confirmation(self, interaction):
        embed = activity_saved_embed(self.activity)
        await interaction.response.send_message(
            content="✅ Activity saved with equipment!",
            embed=embed,
            ephemeral = True
        )

class EquipmentSelectView(View):
    def __init__(self, activity: Activity, user_equipment: List[Equipment]):
        super().__init__(timeout=30)
        self.activity = activity

        options = [
            discord.SelectOption(
                label=eq.name,
                value=str(eq.id),
                description=f"{eq.type.value} ({eq.distance_used}km used, {eq.times_used} times)"
            ) for eq in user_equipment
                if not eq.retired and (eq.sport == activity.sport or eq.sport == Sport.ALL)
        ]

        if options:
            self.add_item(discord.ui.Select(
                placeholder="Select equipment used...",
                options=options,
                min_values=0,
                max_values=len(options),
                custom_id="equipment"
            ))

    async def interaction_check(self, interaction: discord.Interaction):
        if self.children:
            selected_ids = [int(id_str) for id_str in self.children[0].values]
            self.activity.equipment_used = [
                eq for eq in get_equipments(interaction.user.id) if eq.id in selected_ids
            ]

        add_activity(self.activity)
        await self.send_confirmation(interaction)
        self.stop()

    async def send_confirmation(self, interaction):
        embed = activity_saved_embed(self.activity)
        await interaction.response.send_message(
            content="✅ Activity saved with equipment!",
            embed=embed,
            ephemeral = True
        )

def activity_saved_embed(activity: Activity):
    distance_str = format_distance(activity.distance, activity.sport)
    equipment_str = ""
    if hasattr(activity, "equipment_used") and activity.equipment_used:
        equipment_list = getattr(activity, "equipment_used", [])
        equipment_str = ", ".join([f"{eq.name} ({eq.type.value})" for eq in activity.equipment_used]) or "None"

    embed = discord.Embed(
        title="✅ Activity Saved!",
        description=f"Great job on **{activity.title}** {'today' if activity.date == datetime.now().date() else 'on ' + date_to_string(activity.date)}!",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Sport",
        value=f"{activity.sport.value.capitalize()}",
        inline=True
    )
    embed.add_field(
        name="Type",
        value=f"{activity.activity_type.value.capitalize()}" if hasattr(activity, "activity_type") else "N/A",
        inline=True
    )
    embed.add_field(
        name="Date",
        value=f"{date_to_string(activity.date)}",
        inline=True
    )
    embed.add_field(
        name="Start Time",
        value=f"{start_time_to_string(activity.start_time)}",
        inline=True
    )
    embed.add_field(
        name="Duration",
        value=f"{activity.duration}",
        inline=True
    )
    embed.add_field(
        name="Distance",
        value=distance_str,
        inline=True
    )
    if activity.sport != Sport.SWIM:
        embed.add_field(
            name="Elevation Gain",
            value=f"{activity.elevation_gain}m",
            inline=True
        )
    embed.add_field(
        name="RPE",
        value=f"{activity.rpe}",
        inline=True
    )
    if activity.avg_heart_rate > 0:
        embed.add_field(
            name="Avg HR",
            value=f"{activity.avg_heart_rate}bpm",
            inline=True
        )
    if activity.max_heart_rate > 0:
        embed.add_field(
            name="Max HR",
            value=f"{activity.max_heart_rate}bpm",
            inline=True
        )
    if equipment_str:
        embed.add_field(
            name="Equipment Used",
            value=equipment_str,
            inline=False
        )
    if activity.location:
        embed.add_field(
            name="Location",
            value=activity.location,
            inline=True
        )
    if activity.weather:
        embed.add_field(
            name="Weather",
            value=activity.weather,
            inline=True
        )
    if activity.feelings:
        embed.add_field(
            name="Feelings",
            value=activity.feelings,
            inline=False
        )
    if activity.description:
        embed.add_field(
            name="Description",
            value=f"{activity.description}",
            inline=False
        )
    embed.set_footer(text="Your future self will thank you! 💪")
    return embed

class AddActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_activity", description="Add an activity")
    async def add_activity(self, interaction: discord.Interaction):
        view = AddActivityView(interaction.context)
        await interaction.response.send_message("What sport?", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AddActivity(bot))