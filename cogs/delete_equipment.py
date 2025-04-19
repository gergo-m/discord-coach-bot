import discord.ui
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ui import Select

from database import get_equipments, retire_equipment, delete_equipment
from utils import format_duration


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, equipment_id):
        super().__init__(timeout=30)
        self.equipment_id = equipment_id

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.grey)
    async def confirm(self, interaction, button):
        delete_equipment(self.equipment_id)
        await interaction.response.edit_message(
            content="✅ Equipment deleted.",
            view=None
        )
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="❌ Deletion cancelled.",
            view=None
        )
        self.stop()

    @discord.ui.button(label="⚠️ Retire instead!", style=discord.ButtonStyle.green)
    async def retire(self, interaction, button):
        retire_equipment(self.equipment_id)
        await interaction.response.edit_message(
            content="✅ Equipment retired.",
            view=None
        )
        self.stop()

class DeleteEquipmentSelect(Select):
    def __init__(self, equipments):
        options = []
        for equipment in equipments:
            label = f"{equipment.name} ({equipment.type.value})"
            description = f"{equipment.model} - {equipment.distance_used}km ({format_duration(equipment.time_used)}, {equipment.times_used} times)"
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(equipment.id),
                    description=description
                )
            )
        super().__init__(
            placeholder="Select an equipment to delete...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: Interaction):
        equipment_id = int(self.values[0])
        await interaction.response.send_message(
            content="Are you sure you want to delete this equipment?\nYou can **retired it** instead!",
            view=ConfirmDeleteView(equipment_id)
        )

class DeleteEquipmentView(discord.ui.View):
    def __init__(self, equipments):
        super().__init__(timeout=30)
        self.add_item(DeleteEquipmentSelect(equipments))

class DeleteEquipment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="deleteequipment", description="Delete one of your equipments!")
    async def deleteequipment(self, interaction: Interaction):
        equipments = get_equipments(interaction.user.id)

        if not equipments:
            await interaction.response.send_message(
                "You have no equipment to delete!",
                ephemeral=True
            )
            return

        view = DeleteEquipmentView(equipments)
        await interaction.response.send_message(
            "Which equipment would you like to delete?",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(DeleteEquipment(bot))

