from datetime import datetime

import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

from database import add_equipment
from models import Equipment, EquipmentType, Sport
from utils import is_equipment_appropriate, date_from_string, date_to_string


class SelectSportView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

        sport_config = {
            Sport.SWIM: {
                "style": discord.ButtonStyle.blurple,
                "emoji": "🏊"
            },
            Sport.BIKE: {
                "style": discord.ButtonStyle.green,
                "emoji": "🚵"
            },
            Sport.RUN: {
                "style": discord.ButtonStyle.red,
                "emoji": "🏃"
            }
        }

        for sport in Sport:
            if sport == Sport.ALL:
                continue

            config = sport_config.get(sport, {})
            self.add_item(
                Button(
                    label=sport.value.capitalize(),
                    style=config.get("style", discord.ButtonStyle.secondary),
                    emoji=config.get("emoji", ""),
                    custom_id=f"sport_{sport.value}",
                )
            )

    async def interaction_check(self, interaction: discord.Interaction):
        sport_value = interaction.data["custom_id"].split("_")[1]
        sport = Sport(sport_value)
        view = EquipmentTypeSelectView(sport)
        await interaction.response.send_message(view=view)
        return False

class EquipmentTypeSelectView(View):
    def __init__(self, sport: Sport):
        super().__init__()
        self.sport = sport

        options = [
            discord.SelectOption(
                label=etype.value.capitalize(),
                value=etype.value,
                description=f"Select for {etype.value} equipment"
            ) for etype in EquipmentType if is_equipment_appropriate(etype, self.sport)
        ]

        self.add_item(discord.ui.Select(
            placeholder="Choose equipment type...",
            options = options,
            custom_id="equipment_type"
        ))

    async def interaction_check(self, interaction: Interaction):
        selected_type = EquipmentType(self.children[0].values[0])
        modal = EquipmentDetailsModal(interaction.context, selected_type, self.sport)
        await interaction.response.send_modal(modal)

class EquipmentDetailsModal(Modal):
    def __init__(self, ctx, equipment_type: EquipmentType, sport: Sport):
        super().__init__(title=f"🔮 {equipment_type.value.capitalize()} Equipment Details")
        self.ctx = ctx
        self.equipment_type = equipment_type
        self.sport = sport

        self.name_input = TextInput(
            label="🎖️ Name",
            placeholder="Red bike? Trusty shoes?",
        )
        self.model_input = TextInput(
            label="📝 Model",
            placeholder="Bianchi Via Nirone 7? ASICS GT-1200?",
        )
        self.date_input = TextInput(
            label="🗓️ When did you buy it? (yyyy-mm-dd)",
            placeholder="Tip: leave empty for 'today'",
            required=False
        )

        self.add_item(self.name_input)
        self.add_item(self.model_input)
        self.add_item(self.date_input)

    async def on_submit(self, interaction: discord.Interaction):
        # TODO validate date
        date = date_from_string(self.date_input.value) if self.date_input.value else datetime.now().date()

        equipment = Equipment(
            user_id=interaction.user.id,
            name=self.name_input.value,
            model=self.model_input.value,
            sport=self.sport,
            type=self.equipment_type,
            bought_on=date
        )

        embed = discord.Embed(
            title="✅ Equipment Saved!",
            description=f"Nice one! Your **{equipment.type.value}** called **{equipment.name}** was added to your profile.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Name",
            value=f"{equipment.name}",
            inline=True
        )
        embed.add_field(
            name="Sport",
            value=f"{equipment.sport.value.capitalize()}",
            inline=True
        )
        embed.add_field(
            name="Type",
            value=f"{equipment.type.value.capitalize()}",
            inline=True
        )
        embed.add_field(
            name="Distance Used",
            value=f"{equipment.distance_used}",
            inline=True
        )
        embed.add_field(
            name="Time Used",
            value=f"{equipment.time_used}",
            inline=True
        )
        embed.add_field(
            name="Times Used",
            value=f"{equipment.times_used}",
            inline=True
        )
        embed.add_field(
            name="Bought on",
            value=f"{date_to_string(equipment.bought_on)}",
            inline=True
        )

        add_equipment(equipment)
        await interaction.response.send_message(embed=embed)

class AddEquipment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addequipment", description="Add an equipment")
    async def add_equipment(self, interaction: Interaction):
        view = SelectSportView(interaction.context)
        await interaction.response.send_message("Which sport is this equipment used in?", view=view)

async def setup(bot):
    await bot.add_cog(AddEquipment(bot))
