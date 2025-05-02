import shlex
from datetime import datetime, timedelta, time, date
from discord.ext import commands
from models import Sport, Activity, Equipment, ActivityType, EquipmentType
from database import add_activity, add_equipment, get_equipment_by_id


class QuickAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quickadd(self, ctx, *, line):
        """Add activities/equipment with one command:
        !quickadd activity sport=run date=2025-05-01 start=07:30 title="Morning Run" type=workout distance=10.0 elevation_gain=50 duration=00:45:00 rpe=7
        !quickadd equipment name="Speedo" model="Fastskin" sport=swim type=goggles
        """
        try:
            # Split command with proper quote handling
            args = shlex.split(line, posix=True)
            cmd_type = args[0].lower()
            params = {}
            for arg in args[1:]:
                if '=' not in arg:
                    raise ValueError(f"Argument '{arg}' is missing '='. Example: key=value")
                k, v = arg.split('=', 1)
                params[k.lower()] = v.strip('\"\'')

            if cmd_type == "activity":
                equipment_ids = []
                if 'equipment' in params:
                    equipment_ids = [int(eid.strip()) for eid in params['equipment'].split(',')]
                # validate equipment exists and matches sport
                valid_equipment = []
                activity_sport = Sport[params["sport"].upper()]
                for eid in equipment_ids:
                    eq = get_equipment_by_id(eid, int(params.get("user_id", ctx.author.id)))
                    if not eq:
                        raise ValueError(f"Equipment ID {eid} not found")
                    if eq.sport != activity_sport:
                        raise ValueError(f"Equipment ID {eid} is for {eq.sport.value}, not {activity_sport.value}")
                    valid_equipment.append(eq)

                # create and save activity
                activity = Activity(
                    user_id=int(params.get("user_id", ctx.author.id)),
                    sport=Sport(params["sport"]),
                    date=datetime.strptime(params["date"], "%Y-%m-%d").date(),
                    start_time=datetime.strptime(params["start"], "%H:%M").time(),
                    title=params["title"],
                    activity_type=ActivityType(params["type"]),
                    distance=float(params["distance"]),
                    elevation_gain=int(params.get("elevation_gain", 0)),
                    duration=parsed_duration(params["duration"]),
                    rpe=int(params["rpe"]),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                activity.equipment_used = [
                    eq for eq in valid_equipment
                ]
                add_activity(activity)
                await ctx.send(f"Added activity: {params['title']} ({params['sport']})")

            elif cmd_type == "equipment":
                equipment = Equipment(
                    user_id=int(params.get("user_id", ctx.author.id)),
                    name=params["name"],
                    model=params["model"],
                    sport=Sport(params["sport"]),
                    type=EquipmentType(params["type"]),
                    bought_on=date.today(),
                    added_at=datetime.now(),
                    updated_at=datetime.now()
                )
                add_equipment(equipment)
                await ctx.send(f"Added equipment: {params['name']} ({params['sport']})")

            else:
                await ctx.send("Invalid type. Use 'activity' or 'equipment'")

        except Exception as e:
            await ctx.send(f"Error: {str(e)}\nExample usage:\n"
                           "!quickadd activity sport=run date=2025-05-01 start=07:30 title=\"Morning Run\" type=workout distance=10.0 elevation_gain=50 duration=00:45:00 rpe=7\n"
                           "!quickadd equipment name=\"Speedo\" model=\"Fastskin\" sport=swim type=goggles")

def parsed_duration(duration_str: str) -> timedelta:
    parts = list(map(int, duration_str.split(':')))
    if len(parts) == 3:  # HH:MM:SS
        return timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
    elif len(parts) == 2:  # MM:SS
        return timedelta(minutes=parts[0], seconds=parts[1])
    raise ValueError("Invalid duration format")

class BulkAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)  # Only admins can use this
    async def bulkadd(self, ctx, *, block):
        """
        Bulk import: paste multiple quickadd commands, one per line.
        Example:
        !bulkadd
        activity sport=run date=2025-05-01 ...
        equipment name="Speedo" model="Fastskin" sport=swim type=goggles
        """
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        results = []
        for i, line in enumerate(lines, 1):
            try:
                if line.startswith("#"):
                    continue
                # Call your quickadd logic directly
                # Remove the leading "quickadd" or "!" if present
                if line.lower().startswith("quickadd "):
                    line = line[len("quickadd "):]
                if line.startswith("!quickadd "):
                    line = line[len("!quickadd "):]
                # Simulate a ctx for each line
                await ctx.invoke(ctx.bot.get_command("quickadd"), line=line)
                results.append(f"✅ Line {i}: Success")
            except Exception as e:
                results.append(f"❌ Line {i}: {e}")
        await ctx.send("\n".join(results[:10]) + ("\n...and more." if len(results) > 20 else ""))

async def setup(bot):
    await bot.add_cog(QuickAdd(bot))
    await bot.add_cog(BulkAdd(bot))
