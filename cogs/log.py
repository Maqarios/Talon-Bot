import re
import tempfile
import os

from datetime import datetime, time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config

from utils.database_managers import USERS_DBM

from utils.loggers import get_logger

log = get_logger(__name__)


class LogCog(commands.Cog):
    def __init__(self, bot, users_dbm):
        self.bot = bot
        self.users_dbm = users_dbm

    # Slash Command: /show_gm_activity
    @app_commands.command(
        name="show_gm_activity", description="Show recent GM activity logs."
    )
    @app_commands.describe(
        instigator="The user to show logs for.",
        log_version="The log version of logs to show.",
        start="Start time (format: H or H:M or H:M:S, Style: 24 hour).",
        end="End time (format: H or H:M or H:M:S), (Style: 24 hour (i.e. 0, 8, 16, 23)).",
        victim="The user who was affected (optional).",
        keyword="Keyword to filter logs (optional).",
        visibility="Make results visible to everyone (optional).",
    )
    @app_commands.choices(
        visibility=[
            app_commands.Choice(name="Only Me", value="Only Me"),
            app_commands.Choice(name="Everyone", value="Everyone"),
        ],
        type=[
            app_commands.Choice(name="Spawn", value="spawn"),
            app_commands.Choice(name="Context", value="context"),
            app_commands.Choice(name="Attribute", value="attribute"),
        ],
    )
    async def show_gm_activity(
        self,
        interaction: discord.Interaction,
        instigator: discord.User,
        log_version: str,
        start: str,
        end: str,
        type: str = None,
        victim: discord.User = None,
        visibility: str = "Only Me",
        keyword: str = None,
    ):
        # Check if user has CO, MPO, or AO role
        is_CO = False
        is_MPO = False
        is_AO = False
        for role in interaction.user.roles:
            if role.id == config.CO_ROLE_ID:
                is_CO = True
                break
            elif role.id == config.MPO_ROLE_ID:
                is_MPO = True
                break
            elif role.id == config.AO_ROLE_ID:
                is_AO = True
                break
        if not (is_CO or is_MPO or is_AO):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        # Get Bohemia IDs of instigator
        instigator_bohemia_id = self.users_dbm.read_bohemia_id(instigator.id)
        if not instigator_bohemia_id:
            await interaction.response.send_message(
                f"User {instigator.display_name} does not have a Bohemia ID registered.",
                ephemeral=True,
            )
            return

        # Get Bohemia IDs of victim if provided
        victim_bohemia_id = None
        if victim:
            victim_bohemia_id = self.users_dbm.read_bohemia_id(victim.id)
            if not victim_bohemia_id:
                await interaction.response.send_message(
                    f"User {victim.display_name} does not have a Bohemia ID registered.",
                    ephemeral=True,
                )
                return

        # Parse visibility
        is_ephemeral = visibility == "Only Me"

        await interaction.response.defer(ephemeral=is_ephemeral)

        # Parse start and end times
        start = start.split(":")
        start = time(
            hour=int(start[0]),
            minute=int(start[1]) if len(start) > 1 else 0,
            second=int(start[2]) if len(start) > 2 else 0,
        )
        end = end.split(":")
        end = time(
            hour=int(end[0]),
            minute=int(end[1]) if len(end) > 1 else 0,
            second=int(end[2]) if len(end) > 2 else 0,
        )

        activities = self._list_activities(
            log_file_path=Path(
                config.LOG_DIR_PATH + f"/logs_{log_version}/console.log"
            ),
            instigator_bohemia_id=instigator_bohemia_id,
            start_time=start,
            end_time=end,
            type=type,
            victim_bohemia_id=victim_bohemia_id,
            keyword=keyword,
        )

        tmp_path = None
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as tmp:

            tmp.write(f"Parameters:\n")

            tmp.write(
                f"  Instigator: {instigator.display_name} (ID: {instigator.id})\n"
            )

            tmp.write(f"  Log Version: {log_version}\n")

            tmp.write(f"  Start Time: {start}\n")

            tmp.write(f"  End Time: {end}\n")

            if type:
                tmp.write(f"  Type: {type}\n")

            if victim:
                tmp.write(f"  Victim: {victim.display_name} (ID: {victim.id})\n")

            if keyword:
                tmp.write(f"  Keyword: {keyword}\n")

            tmp.write(f"\nActivities:\n")
            for log_time, logs in activities.items():
                line = f"  Time: {log_time}\n"
                for i, (log_entry, count) in enumerate(logs.values()):
                    entry_type = log_entry["type"]
                    if entry_type == "spawn":
                        line += f"    Entry: Spawned {log_entry['target'].split('/')[-1][:-3]}, (x{count})\n"
                    elif entry_type == "context":
                        name = self.users_dbm.read_by_bohemia_id(log_entry["target"])
                        name = name[2] if name else "N/A"
                        line += f"    Entry: Used {log_entry['action']} on {log_entry['target']} ({name}), (x{count})\n"
                    elif entry_type == "attribute":
                        name = self.users_dbm.read_by_bohemia_id(log_entry["target"])
                        name = name[2] if name else "N/A"
                        line += f"    Entry: Changed {log_entry['attribute']} of {log_entry['target']} ({name}) from {log_entry['before']} to {log_entry['after']}, (x{count})\n"

                tmp.write(line)

            tmp.flush()
            tmp_path = tmp.name

        await interaction.followup.send(
            file=discord.File(tmp_path, filename="result.txt"), ephemeral=is_ephemeral
        )
        os.remove(tmp_path)

    # Autocomplete for log_version parameter
    @show_gm_activity.autocomplete("log_version")
    async def log_version_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        options = []

        # Get directory paths for the user's sections
        logs_dir = Path(config.LOG_DIR_PATH)

        # List all available log versions
        if logs_dir.exists():
            for file_path in sorted(logs_dir.glob(f"logs_*"), reverse=True):
                if file_path.is_dir():
                    options.append(file_path.stem.replace(f"logs_", ""))

        # Filter options based on current input
        choices = []
        if len(options) > 0:
            if current.lower() in options[0].lower():
                name = datetime.strptime(options[0], config.GAME_LOGS_TIME_FORMAT)
                name = f"Date: {name.strftime('%d.%m.%Y')}, Time: {name.strftime('%H:%M:%S')} (current)"

                choices.append(app_commands.Choice(name=name, value=options[0]))

        for opt in options[1:]:
            if current.lower() in opt.lower():
                name = datetime.strptime(opt, config.GAME_LOGS_TIME_FORMAT)
                name = f"Date: {name.strftime('%d.%m.%Y')}, Time: {name.strftime('%H:%M:%S')}"

                choices.append(app_commands.Choice(name=name, value=opt))

        return choices[:25]

    # Assign attributes
    def _assign_attributes(self, log_line: str):
        attributes = {}
        parts = log_line.split(", ")
        for part in parts:
            part = part.split(": ")
            attributes[part[0].strip()] = part[1].strip()

        return attributes

    # Compress Activities
    def _compress_activities(self, activities: dict):
        compressed = {}
        for time, logs in activities.items():
            compressed[time] = {}
            for log in logs:
                if str(log) not in compressed[time]:
                    compressed[time][str(log)] = (log, 0)

                compressed[time][str(log)] = (
                    log,
                    compressed[time][str(log)][1] + 1,
                )

        return compressed

    # Read logs from file
    def _list_activities(
        self,
        log_file_path: Path,
        instigator_bohemia_id: str,
        start_time: time,
        end_time: time,
        type: str,
        victim_bohemia_id: str,
        keyword: str,
    ):
        activities = {}
        if log_file_path.exists() and log_file_path.is_file():
            with open(
                log_file_path, "r", encoding="utf-8", errors="ignore"
            ) as log_file:
                for line in log_file:
                    try:
                        line = line.strip().lower()  # Normalize case
                        line = re.sub(r"\s+", " ", line)  # Clean up whitespace
                        elements = line.split(" | ")  # Split log components
                        if not elements or len(elements) < 3:
                            continue

                        log_time = datetime.strptime(elements[0][:8], "%H:%M:%S").time()
                        if start_time <= log_time <= end_time:
                            if elements[1] != "gm_monitor":
                                continue

                            attributes = self._assign_attributes(elements[2])
                            if instigator_bohemia_id == attributes.get(
                                "instigator", ""
                            ):
                                if type and type != attributes.get("type", ""):
                                    continue

                                if (
                                    victim_bohemia_id
                                    and victim_bohemia_id
                                    != attributes.get("target", "")
                                ):
                                    continue

                                if keyword and keyword not in line:
                                    continue

                                log_time_formatted = log_time.strftime("%H:%M:%S")
                                if log_time_formatted not in activities:
                                    activities[log_time_formatted] = []

                                activities[log_time_formatted].append(attributes)
                    except ValueError as e:
                        log.error(f"Error parsing log line: {line}. Error: {e}")
                        continue
        return self._compress_activities(activities)


async def setup(bot):
    await bot.add_cog(LogCog(bot, USERS_DBM))
