import os
from datetime import datetime, timedelta

import discord.ui
import requests
from discord import app_commands, Interaction, ButtonStyle, Embed
from discord.ext import commands
from discord.types.embed import EmbedMedia

from cogs.add_activity import activity_saved_embed
from database import get_strava_token, add_activity, add_strava_token
from models import StravaToken, Activity, Sport
from utils import STRAVA_TO_SPORT


class Strava(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.redirect_uri = os.getenv('STRAVA_REDIRECT_URI')

    # Add to Strava class in strava.py
    @commands.command()
    async def strava_auth(self, ctx, link: str):
        code = link.split('&')[1][5:]
        try:
            response = requests.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code"
                }
            )
            if response.status_code == 200:
                data = response.json()
                token = StravaToken(
                    user_id=ctx.author.id,
                    strava_user_id=data["athlete"]["id"],
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_at=datetime.now() + timedelta(seconds=data["expires_in"])
                )
                add_strava_token(token)  # Implement this in database.py
                await ctx.send("✅ Strava account connected!", ephemeral=True)
            else:
                await ctx.send("❌ Failed to connect Strava account", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="strava", description="Connect or sync Strava account")
    @app_commands.describe(action="Connect or sync with Strava")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="connect", value="connect"),
            app_commands.Choice(name="sync", value="sync")
        ]
    )
    async def strava(self, interaction: Interaction, action: str = "sync"):
        if action == "connect":
            auth_url = f"https://www.strava.com/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope=activity:read_all"
            await interaction.response.send_message(
                f"Connect your Strava account: [Click Here]({auth_url})\nGo through the authorization process, then type `!strava_auth <link>` with the link you were finally redirected to.",
                ephemeral=True
            )
        elif action == "sync":
            await self.handle_sync(interaction)

    def refresh_token(self, token: StravaToken):
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token
            }
        )
        if response.status_code == 200:
            data = response.json()
            return StravaToken(
                user_id=token.user_id,
                strava_user_id=token.strava_user_id,
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_at=datetime.now() + timedelta(seconds=data["expires_in"])
            )
        return None

    async def handle_sync(self, interaction: Interaction):
        token = get_strava_token(interaction.user.id)
        if not token:
            await interaction.response.send_message(
                "Please connect Strava first",
                ephemeral=True
            )
            return

        if token.expires_at < datetime.now():
            new_token = self.refresh_token(token)
            if new_token:
                add_strava_token(new_token)
                token = new_token
            else:
                await interaction.response.send_message(
                    "Token refresh failed",
                    ephemeral=True
                )
                return

        activities = self.get_recent_activities(token)
        if not activities:
            await interaction.response.send_message(
                "No new activities found on Strava!",
                ephemeral=True
            )
            return

        view = SyncActivitiesView(activities)
        await interaction.response.send_message(
            "Found these recent Strava activities:",
            view=view,
            ephemeral=True
        )

    def get_recent_activities(self, token: StravaToken):
        headers = {"Authorization": f"Bearer {token.access_token}"}
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return None

class SyncActivitiesView(discord.ui.View):
    def __init__(self, activities):
        super().__init__()
        for activity in activities[:5]:
            self.add_item(SyncActivityButton(activity))

class SyncActivityButton(discord.ui.Button):
    def __init__(self, activity):
        super().__init__(
            label=f"{activity['name']} ({activity['type']})",
            style=ButtonStyle.blurple
        )
        self.activity = activity

    async def callback(self, interaction: Interaction):
        converted = self.convert_strava_activity(self.activity, interaction)
        add_activity(converted)

        await interaction.channel.send(
            f"🏅 **New activity from {interaction.user.mention}**",
            embed=activity_saved_embed(converted)
        )
        await interaction.response.edit_message(
            content="Activity posted successfully!",
            view=None
        )

    def convert_strava_activity(self, strava_activity, interaction: Interaction):
        sport: Sport = STRAVA_TO_SPORT[strava_activity['type'].lower()]
        return Activity(
            user_id=interaction.user.id,
            sport=sport,
            date=datetime.strptime(strava_activity['start_date'], "%Y-%m-%dT%H:%M:%SZ").date(),
            start_time=datetime.strptime(strava_activity['start_date'], "%Y-%m-%dT%H:%M:%SZ").time(),
            title=strava_activity['name'],
            distance=strava_activity['distance'] if sport == Sport.SWIM else strava_activity['distance']/1000,
            duration=timedelta(seconds=strava_activity['moving_time']),
            elevation_gain=strava_activity['total_elevation_gain'],
            avg_heart_rate=strava_activity['average_heartrate'] if 'average_heartrate' in strava_activity else 0,
            max_heart_rate=strava_activity['max_heartrate'] if 'max_heartrate' in strava_activity else 0,
            rpe=strava_activity['perceived_exertion'] if 'perceived_exertion' in strava_activity else 0,
            description=strava_activity['description'] if 'description' in strava_activity else "",
        )

    def create_activity_embed(self, activity):
        embed = Embed(
            title=activity.title,
            description=activity.description
        )

async def setup(bot):
    await bot.add_cog(Strava(bot))