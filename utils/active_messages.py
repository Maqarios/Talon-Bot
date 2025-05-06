import sys
import time
import datetime

import discord
from discord.ui import Button, View
from discord.ext import tasks

sys.path.append("..")  # Adjust the path to import config and utils
import config

from utils.cache import ACTIVE_PLAYERS_BOHEMIA_ID_CACHE
from utils.utils import (
    is_port_listening,
    get_server_utilization,
    get_active_messages_id,
    set_active_messages_id,
    format_time_elapsed,
    list_active_mods,
    list_active_players,
)


async def create_empty_message(channel, initial_message="Empty Message"):
    message = await channel.send(initial_message)
    return message


@tasks.loop(minutes=1)
async def create_or_update_server_utilization_status_message(
    bot,
    channel_id,
):
    # Fetch the channel
    try:
        channel = bot.get_channel(channel_id)
    except discord.NotFound:
        print(f"Channel with ID {channel_id} not found.")
        return False
    except discord.Forbidden:
        print(f"Permission denied to access channel {channel_id}.")
        return False

    # Fetch the message
    message_id = None
    message = None
    try:
        message_id = get_active_messages_id(
            config.ACTIVEMESSAGESIDS_PATH, "server_utilization_status_message_id"
        )
        message = await channel.fetch_message(message_id)
    except (FileNotFoundError, KeyError, discord.NotFound) as e:
        message = await create_empty_message(
            channel, "Creating a new message for team members status."
        )
        set_active_messages_id(
            config.ACTIVEMESSAGESIDS_PATH,
            "server_utilization_status_message_id",
            message.id,
        )
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    # Update the message content
    refresh_button = Button(
        style=discord.ButtonStyle.secondary,
        emoji="🔄",
        custom_id="refresh_server_utilization_status_message",
    )
    view = View(timeout=None)
    view.add_item(refresh_button)

    # Create Discord embed for better formatting
    embed = discord.Embed(
        title="Server Utilization",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now(),
    )

    # Get CPU, memory, and disk usage
    cpu, memory, disk = get_server_utilization()
    if (
        (isinstance(cpu, float) and cpu > 70)
        or (isinstance(memory, float) and memory > 85)
        or (isinstance(disk, float) and disk > 80)
    ):
        embed.color = discord.Color.red()

    # Add fields to the embed
    embed.add_field(name="CPU Usage", value=f"{cpu:.2f}%", inline=True)
    embed.add_field(name="Memory Usage", value=f"{memory:.2f}%", inline=True)
    embed.add_field(name="Disk Usage", value=f"{disk:.2f}%", inline=True)

    # Add footer with timestamp
    embed.set_footer(text="Last updated")

    # Edit the message with the new content
    try:
        await message.edit(content=None, embed=embed, view=view)
    except discord.NotFound:
        time.sleep(config.SLEEP_TIME)
        create_or_update_server_utilization_status_message(bot, channel_id)
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    return True


async def create_or_update_teams_members_status_message(
    bot,
    channel_id,
    user_dbm,
):
    # Fetch the channel
    try:
        channel = bot.get_channel(channel_id)
    except discord.NotFound:
        print(f"Channel with ID {channel_id} not found.")
        return False
    except discord.Forbidden:
        print(f"Permission denied to access channel {channel_id}.")
        return False

    # Fetch the message
    message_id = None
    message = None
    try:
        message_id = get_active_messages_id(
            config.ACTIVEMESSAGESIDS_PATH, "teams_members_status_message_id"
        )
        message = await channel.fetch_message(message_id)
    except (FileNotFoundError, KeyError, discord.NotFound) as e:
        message = await create_empty_message(
            channel, "Creating a new message for team members status."
        )
        set_active_messages_id(
            config.ACTIVEMESSAGESIDS_PATH, "teams_members_status_message_id", message.id
        )
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    # Update the message content
    refresh_button = Button(
        style=discord.ButtonStyle.secondary,
        emoji="🔄",
        custom_id="refresh_teams_members_status_message",
    )
    view = View(timeout=None)
    view.add_item(refresh_button)

    # Create Discord embed for better formatting
    embed = discord.Embed(
        title="Team Status",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now(),
    )

    # Get data from database
    users = user_dbm.get_users_for_active_message()

    # Group users by team
    teams = {team: [] for team in config.TEAMS}
    for user_displayname, user_status, user_team, user_joined in users:
        if (
            user_status == "Active"
            and user_team in config.TEAMS
            and user_team != "Red Talon"
        ):
            teams[user_team].append((user_displayname, user_joined))
    # Add each team as a field in the embed
    for team_name, members in teams.items():

        # Join member names with newlines
        member_list = "\n".join(
            [
                f"• {member} ({format_time_elapsed(joined)})"
                for member, joined in members
            ]
        )

        # If no members, set to "No members"
        if not member_list:
            member_list = "No members"

        # Add the team to the embed
        embed.add_field(name=team_name, value=member_list, inline=True)

    # Add footer with timestamp
    embed.set_footer(text="Last updated")

    # Edit the message with the new content
    try:
        await message.edit(content=None, embed=embed, view=view)
    except discord.NotFound:
        time.sleep(config.SLEEP_TIME)
        create_or_update_teams_members_status_message(bot, channel_id, user_dbm)
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    return True


@tasks.loop(minutes=1)
async def create_or_update_active_players_on_gameserver_status_message(
    bot,
    channel_id,
    server_stats,
):
    # Fetch the channel
    try:
        channel = bot.get_channel(channel_id)
    except discord.NotFound:
        print(f"Channel with ID {channel_id} not found.")
        return False
    except discord.Forbidden:
        print(f"Permission denied to access channel {channel_id}.")
        return False

    # Fetch the message
    message_id = None
    message = None
    try:
        message_id = get_active_messages_id(
            config.ACTIVEMESSAGESIDS_PATH,
            "active_players_on_gameserver_status_message_id",
        )
        message = await channel.fetch_message(message_id)
    except (FileNotFoundError, KeyError, discord.NotFound) as e:
        message = await create_empty_message(
            channel, "Creating a new message for team members status."
        )
        set_active_messages_id(
            config.ACTIVEMESSAGESIDS_PATH,
            "active_players_on_gameserver_status_message_id",
            message.id,
        )
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    # Create Discord embed for better formatting
    embed = discord.Embed(
        title="Server is Online",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now(),
    )

    # Get gameserver online status
    gameserver_status = is_port_listening(config.GAMESERVER_PORT)

    if not gameserver_status:
        embed.title = "Server is Offline"
        embed.color = discord.Color.red()
    else:
        # Define the field to be added
        field = {"name": "", "value": "", "inline": False}

        if server_stats.players == -1:
            embed.color = discord.Color.red()
            field["name"] = "Something went wrong. Contact the server administrator."
        if server_stats.players == 0:
            embed.color = discord.Color.yellow()
            field["name"] = "No Active Players"
        else:
            field["name"] = f"Active Players: {server_stats.players}"
            field["value"] = "\n".join(
                [f"• {player}" for player in server_stats.connected_players.values()]
            )

            for (
                player_bohemia_id,
                player_name,
            ) in server_stats.connected_players.items():
                ACTIVE_PLAYERS_BOHEMIA_ID_CACHE.handle_player(
                    player_bohemia_id, player_name
                )

        embed.add_field(**field)

    # Add footer with timestamp
    embed.set_footer(text="Last updated")

    # Edit the message with the new content
    try:
        await message.edit(content=None, embed=embed)
    except discord.NotFound:
        time.sleep(config.SLEEP_TIME)
        create_or_update_active_players_on_gameserver_status_message(bot, channel_id)
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    return True


class UserTrackerActiveMessages:
    def __init__(self, bot, channel_id, db):
        self.bot = bot
        self.channel_id = channel_id
        self.db = db
        self.active_messages = {}

    async def create_status_message(self):
        channel = self.bot.get_channel(self.channel_id)

        # Create refresh button
        refresh_button = Button(
            style=discord.ButtonStyle.secondary,
            emoji="🔄",
            custom_id="refresh_team_status",
        )
        view = View(timeout=None)
        view.add_item(refresh_button)

        # Initial empty message with button
        message = await channel.send("Loading team status...", view=view)
        self.active_messages["status"] = message.id

        # Update the message content
        await self.update_status_message()

    async def update_status_message(self):
        if "status" not in self.active_messages:
            await self.create_status_message()

        channel = self.bot.get_channel(self.channel_id)
        try:
            message = await channel.fetch_message(self.active_messages["status"])

            # Get data from database
            users = self.db.get_users_for_active_message()

            # Group users by team
            teams = {team: [] for team in config.TEAMS}
            for user_displayname, user_status, user_team, user_joined in users:
                if user_status == "Active" and user_team in config.TEAMS:
                    teams[user_team].append((user_displayname, user_joined))

            # Create Discord embed for better formatting
            embed = discord.Embed(
                title="Team Status",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(),
            )

            # Add each team as a field in the embed
            for team_name, members in teams.items():
                if team_name == "Red Talon":
                    continue

                # Join member names with newlines
                member_list = "\n".join(
                    [
                        f"• {member} ({format_time_elapsed(joined)})"
                        for member, joined in members
                    ]
                )
                if not member_list:
                    member_list = "No members"

                # Use inline=True to create columns
                embed.add_field(name=team_name, value=member_list, inline=True)

                # Add empty spacer field
                # embed.add_field(name="\u200b", value="\u200b", inline=True)

            # Add footer with timestamp
            embed.set_footer(text="Last updated")

            await message.edit(content=None, embed=embed)
        except discord.NotFound:
            # Message was deleted, create a new one
            await self.create_status_message()

    async def shutdown(self):
        # Delete tracked messages
        for msg_type, msg_id in self.active_messages.items():
            try:
                channel = self.bot.get_channel(self.channel_id)
                message = await channel.fetch_message(msg_id)
                await message.delete()
                print(f"✅ Deleted message: {msg_type}, Channel: {self.channel_id}")
            except:
                print(
                    f"❌ Failed to delete message: {msg_type}, Channel: {self.channel_id}"
                )


class GreenTeamActiveMessages:
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.active_messages = {}

    async def create_join_green_team_message(self):
        channel = self.bot.get_channel(self.channel_id)

        # Create refresh button
        refresh_button = Button(
            style=discord.ButtonStyle.secondary,
            emoji="🟩",
            custom_id="join_green_team",
        )
        view = View(timeout=None)
        view.add_item(refresh_button)

        # Initial empty message with button
        message = await channel.send("Loading Join Green Team Message...", view=view)
        self.active_messages["message"] = message.id

        # Create Discord embed for better formatting
        embed = discord.Embed(
            title="React with 🟩 to join Green Team",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(),
        )
        await message.edit(content=None, embed=embed)

    async def shutdown(self):
        # Delete tracked messages
        for msg_type, msg_id in self.active_messages.items():
            try:
                channel = self.bot.get_channel(self.channel_id)
                message = await channel.fetch_message(msg_id)
                await message.delete()
                print(f"✅ Deleted message: {msg_type}, Channel: {self.channel_id}")
            except:
                print(
                    f"❌ Failed to delete message: {msg_type}, Channel: {self.channel_id}"
                )


class ActiveModsActiveMessages:
    def __init__(self, bot, channel_id, serverconfig_path):
        self.bot = bot
        self.channel_id = channel_id
        self.serverconfig_path = serverconfig_path
        self.active_messages = {}

    @tasks.loop(hours=24)
    async def update_active_mods_message(self):
        # Delete all previously tracked messages
        channel = self.bot.get_channel(self.channel_id)
        for msg_type, msg_id in list(self.active_messages.items()):
            try:
                old_message = await channel.fetch_message(msg_id)
                await old_message.delete()
                del self.active_messages[msg_type]  # Remove from tracking
            except discord.NotFound:
                # Message was already deleted
                del self.active_messages[msg_type]

        # Get active mods from serverconfig
        active_mods = sorted(list_active_mods(self.serverconfig_path))

        # Format the active mods as a plain text message
        if not active_mods:
            content = "No Active Mods"
            new_message = await channel.send(content)
            self.active_messages["message"] = new_message.id
            return

        # Split the active mods into chunks based on cumulative character length
        max_length = 2000  # Discord's character limit
        chunks = []
        current_chunk = []
        current_length = 0

        for mod in active_mods:
            mod_entry = f"• {mod}\n"
            if current_length + len(mod_entry) > max_length:
                # Start a new chunk if adding this mod exceeds the limit
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(mod_entry)
            current_length += len(mod_entry)

        # Add the last chunk
        if current_chunk:
            chunks.append("".join(current_chunk))

        # Send new messages for each chunk and track them
        for i, chunk in enumerate(chunks):
            new_message = await channel.send(chunk)
            self.active_messages[f"message_{i}"] = new_message.id

    async def shutdown(self):
        # Delete tracked messages
        for msg_type, msg_id in self.active_messages.items():
            try:
                channel = self.bot.get_channel(self.channel_id)
                message = await channel.fetch_message(msg_id)
                await message.delete()
                print(f"✅ Deleted message: {msg_type}, Channel: {self.channel_id}")
            except:
                print(
                    f"❌ Failed to delete message: {msg_type}, Channel: {self.channel_id}"
                )


class ActivePlayersActiveMessages:
    def __init__(self, bot, channel_id, serverstats_path):
        self.bot = bot
        self.channel_id = channel_id
        self.serverstats_path = serverstats_path
        self.active_messages = {}

    @tasks.loop(minutes=5)
    async def update_active_players_message(self):
        channel = self.bot.get_channel(self.channel_id)

        if "status" not in self.active_messages:
            view = View(timeout=None)

            # Initial empty message
            message = await channel.send("Loading current active players...", view=view)
            self.active_messages["status"] = message.id

        try:
            message = await channel.fetch_message(self.active_messages["status"])

            # Get data from database
            active_players = sorted(list_active_players(self.serverstats_path))

            # Create Discord embed for better formatting
            embed = discord.Embed(
                title="Players Online",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(),
            )

            if not active_players:
                embed.add_field(
                    name=f"Active Players: {len(active_players)}",
                    value="",
                )
            else:
                embed.add_field(
                    name=f"Active Players: {len(active_players)}",
                    value="\n".join([f"• {player}" for player in active_players]),
                    inline=False,
                )

            # Add footer with timestamp
            embed.set_footer(text="Last updated")

            await message.edit(content=None, embed=embed)
        except discord.NotFound:
            # Message was deleted, create a new one
            await self.create_active_players_message()

    async def shutdown(self):
        # Delete tracked messages
        for msg_type, msg_id in self.active_messages.items():
            try:
                channel = self.bot.get_channel(self.channel_id)
                message = await channel.fetch_message(msg_id)
                await message.delete()
                print(f"✅ Deleted message: {msg_type}, Channel: {self.channel_id}")
            except:
                print(
                    f"❌ Failed to delete message: {msg_type}, Channel: {self.channel_id}"
                )
