import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import View, Select

from database import retire_equipment, get_equipments
from utils import format_duration, date_to_string


class ConfirmUnretireView(View):
    def __init__(self, equipment_id):
        super().__init__(timeout=30)
        self.equipment_id = equipment_id

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.grey)
    async def confirm(self, interaction, button):
        retire_equipment(self.equipment_id)
        await interaction.response.edit_message(
            content="✅ Equipment unretired.",
            view=None
        )
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="❌ Unretirement cancelled.",
            view=None
        )
        self.stop()


class UnretireEquipmentSelect(Select):
    def __init__(self, equipments):
        options = []
        for equipment in equipments:
            label = f"{equipment.name} ({equipment.type.value}) - Retired on {date_to_string(equipment.retired_on)}"
            description = f"{equipment.model} - {equipment.distance_used}km ({format_duration(equipment.time_used)}, {equipment.times_used} times)"
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(equipment.id),
                    description=description
                )
            )
        super().__init__(
            placeholder="Select an equipment to unretire...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction):
        equipment_id = int(self.values[0])
        await interaction.response.send_message(
            content="Are you sure you want to unretire this equipment?",
            view=ConfirmUnretireView(equipment_id),
            ephemeral=True
        )


class UnretireEquipmentView(View):
    def __init__(self, equipments):
        super().__init__(timeout=30)
        self.add_item(UnretireEquipmentSelect(equipments))


class UnretireEquipment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unretire_equipment", description="Unretire one of your retired equipment!")
    async def unretireequipment(self, interaction: Interaction):
        equipments = [e for e in get_equipments(interaction.user.id) if e.retired]

        if not equipments:
            await interaction.response.send_message(
                "You have no equipment to unretire!",
                ephemeral=True
            )
            return

        view = UnretireEquipmentView(equipments)
        await interaction.response.send_message(
            "Which equipment would you like to unretire?",
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(UnretireEquipment(bot))
