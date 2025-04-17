import re

import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

workouts = {}

class AddWorkoutView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @discord.ui.button(label="Swim", style=discord.ButtonStyle.blurple)
    async def swim_button(self, interaction: discord.Interaction, button: Button):
        modal = TitleInputModal(self.ctx, "swim")
        await interaction.response.send_modal(modal)


class TitleInputModal(Modal):
    def __init__(self, ctx, sport):
        super().__init__(title=f"🎉 {sport.capitalize()} Workout Details")
        self.ctx = ctx
        self.sport = sport

        self.start_input = TextInput(
            label="Start time (hh:mm)",
            placeholder="Early riser? 05:07 | After work? 16:47"
        )
        self.title_input = TextInput(
            label="Title",
            placeholder="Peaceful run on the beach... or self-torture in the rain?",
            max_length=50
        )
        self.distance_input = TextInput(
            label=f"Distance ({'km' if sport != 'swim' else 'meters'})",
            placeholder="Marathon? 42.2 | Sprint? 0.1 | Pool laps? 1500"
        )
        self.time_input = TextInput(
            label="Duration (hh:mm:ss)",
            placeholder="Speedy? 00:18:32 | Scenic route? 01:45:23"
        )
        self.description_input = TextInput(
            label="Tell me all about it!",
            placeholder="Felt unstoppable? Drowned in sweat?",
            style=discord.TextStyle.long,
            required=False
        )

        self.add_item(self.start_input)
        self.add_item(self.title_input)
        self.add_item(self.distance_input)
        self.add_item(self.time_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        # validate time
        if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$", self.time_input.value):
            return await interaction.response.send_message(
                "⏰ Whoa time traveler! Use `hh:mm:ss` format (e.g. 01:30:45)",
                ephemeral=True
            )

        # validate start
        if not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", self.start_input.value):
            return await interaction.response.send_message(
                "⏰ Please use `hh:mm` 24-hour format (e.g. 05:07, 16:47)",
                ephemeral=True
            )

        # validate distance
        try:
            distance = float(self.distance_input.value)
            if distance <= 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "📏 Distance needs to be a positive number!",
                ephemeral=True
            )

        # create workout data dictionary
        workout_data = {
            "user_id": interaction.user.id,
            "sport": self.sport,
            "start": self.start_input.value,
            "title": self.title_input.value,
            "distance": self.distance_input.value,
            "duration": self.time_input.value,
            "description": self.description_input.value
        }

        # RPE selection
        await interaction.response.send_message(
            "How hard did this workout feel? (Rate 1-10)",
            view=RPEView(workout_data),
            ephemeral=True
        )

class RPEView(View):
    def __init__(self, workout_data):
        super().__init__(timeout=30)
        self.workout_data = workout_data

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
        self.workout_data["rpe"] = rpe
        # db save logic TODO

        # confirmation
        embed = discord.Embed(
            title="✅ Workout Saved!",
            description=f"Great job on **{self.workout_data["title"]}** today!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Start Time",
            value=f"{self.workout_data["start"]}",
            inline=True
        )
        embed.add_field(
            name="Sport",
            value=f"{self.workout_data["sport"].capitalize()}",
            inline=True
        )
        embed.add_field(
            name="Duration",
            value=f"{self.workout_data["duration"]}",
            inline=True
        )
        embed.add_field(
            name="Distance",
            value=f"{self.workout_data["distance"]}{'km' if self.workout_data["sport"] != 'swim' else 'm'}",
            inline=True
        )
        embed.add_field(
            name="RPE",
            value=f"{self.workout_data['rpe']}",
            inline=True
        )
        if self.workout_data["description"]:
            embed.add_field(
                name="Description",
                value=f"{self.workout_data["description"]}",
                inline=False
            )
        embed.set_footer(text="Your future self will thank you! 💪")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

class AddWorkout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="addWorkout")
    async def add_workout(self, ctx):
        view = AddWorkoutView(ctx)
        await ctx.send("What sport?", view=view)

async def setup(bot):
    await bot.add_cog(AddWorkout(bot))