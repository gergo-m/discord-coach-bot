import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

from database import get_equipments
from models import Sport
from utils import format_distance, format_duration, date_to_string, date_from_string, format_timedelta, SPORT_EMOJI, \
    SPORT_BUTTON_STYLE


class GetEquipmentsView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

        for sport in Sport:
            self.add_item(
                Button(
                    label=sport.value.capitalize(),
                    style=SPORT_BUTTON_STYLE[sport],
                    emoji=SPORT_EMOJI[sport],
                    custom_id=f"sport_{sport.value}",
                )
            )

    def build_embed(self, user_id, sport: Sport, button_style: discord.ButtonStyle):
        color_mapping = {
            discord.ButtonStyle.grey: discord.Color.light_grey(),
            discord.ButtonStyle.blurple: discord.Color.blurple(),
            discord.ButtonStyle.green: discord.Color.green(),
            discord.ButtonStyle.red: discord.Color.red()
        }

        equipments = get_equipments(user_id, sport if sport != Sport.ALL else None)

        embed = discord.Embed(
            title=f"🔨 {sport.value.capitalize() if sport != Sport.ALL else 'All'} Equipment",
            color=color_mapping[button_style]
        )
        for equipment in equipments:
            value_lines = [
                f"**Model:** {equipment.model}",
                f"**Sport:** {equipment.sport.value}",
                f"**Distance:** {equipment.distance_used}km",
                f"**Time used:** {format_duration(equipment.time_used)}",
                f"**Times used:** {equipment.times_used}",
                f"**Bought on:** {date_to_string(equipment.bought_on)}",
                f"Added: {equipment.added_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ]

            if equipment.retired:
                value_lines.append(f"🔒 **RETIRED** on {date_to_string(equipment.retired_on)}")

            embed.add_field(
                name=f"{SPORT_EMOJI[equipment.sport]} {equipment.name} ({equipment.type.value})",
                value="\n".join(value_lines),
                inline=True
            )

        if not equipments:
            embed.description = "No equipment found. Add them using `/addequipment`!"
        else:
            embed.set_footer(text=f"Looking good. Put {'them' if len(equipments) > 1 else 'it'} to good use!")
        return embed

    async def interaction_check(self, interaction: discord.Interaction):
        sport_value = interaction.data["custom_id"].split("_")[1]
        button_style = interaction
        sport = Sport(sport_value)
        embed = self.build_embed(interaction.user.id, sport, discord.ButtonStyle.blurple)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

class Equipments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="equipment", description="View your added equipment")
    async def equipments(self, interaction: discord.Interaction):
        view = GetEquipmentsView(interaction.context)
        await interaction.response.send_message(
            "Choose a sport:",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Equipments(bot))