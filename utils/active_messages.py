import time
import datetime

import discord
from discord import InteractionType
from discord.ui import Button, View
from discord.ext import tasks

import config

from utils.cache import ACTIVE_PLAYERS_BOHEMIA_ID_CACHE
from utils.utils import (
    is_port_listening,
    get_server_utilization,
    get_active_messages_id,
    set_active_messages_id,
    format_time_elapsed,
    add_mod_to_serverconfig,
    update_mod_version_in_serverconfig,
    remove_mod_from_serverconfig,
    get_channel,
)
from utils.website_scarpers import (
    WorkshopModPageWebsiteScarper,
    WorkshopModSearchWebsiteScarper,
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
        embed.add_field(name=team_name, value=member_list, inline=False)

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
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False
    except Exception as e:
        print(f"Unknown Exception: {e}")
        return False

    return True


class ModsActiveMessages:
    def __init__(self, bot, channel_id, server_config):
        self.bot = bot
        self.channel_id = channel_id
        self.server_config = server_config

        self.channel = None
        self.messages_cache = {}
        self.mod_idx = -1  # Used to track the index of the mod being processed

    def make_mod_message(self, mod_id):
        # Get mod details
        workshop_scarper = WorkshopModPageWebsiteScarper(mod_id)
        # TODO: handle if mod is not found

        # Create Discord embed for better formatting
        embed = discord.Embed(
            title="Mod Details",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )

        # Create the view with buttons
        view = View(timeout=None)

        # Create buttons
        update_button = Button(
            style=discord.ButtonStyle.green,
            label="Update Mod",
            custom_id="update_mod:{}:{}".format(mod_id, workshop_scarper.version),
        )
        check_button = Button(
            style=discord.ButtonStyle.blurple,
            label="Check for updates",
            custom_id="check_mod:{}".format(mod_id),
        )
        delete_button = Button(
            style=discord.ButtonStyle.red,
            label="Remove Mod",
            custom_id="remove_mod:{}".format(mod_id),
        )

        if (
            self.server_config.game.searchable_mods[mod_id]["version"]
            != workshop_scarper.version
        ):
            embed.title = "{} (Update Available)".format(workshop_scarper.name)
            embed.color = discord.Color.blue()
            embed.description = "**Version: {} ⟶ {}**\n[Workshop Link]({})".format(
                self.server_config.game.searchable_mods[mod_id]["version"],
                workshop_scarper.version,
                config.WORKSHOP_MOD_PAGE_URL + mod_id,
            )

            view.add_item(update_button)
            view.add_item(check_button)
            view.add_item(delete_button)

        else:
            embed.title = "{}".format(workshop_scarper.name)
            embed.color = discord.Color.green()
            embed.description = "**Version: {}**\n[Workshop Link]({})".format(
                workshop_scarper.version, config.WORKSHOP_MOD_PAGE_URL + mod_id
            )

            view.add_item(check_button)
            view.add_item(delete_button)

        if workshop_scarper.dependencies:
            dependency_content = ""

            for (
                dependency_id,
                dependency_details,
            ) in workshop_scarper.dependencies.items():
                dependency_content += "{}\n".format(dependency_details["name"])

            embed.add_field(
                name="Dependencies",
                value=dependency_content,
                inline=False,
            )

        return embed, view

    def make_mod_search_message(self, search_query):
        # Get mod details
        workshop_scarper = WorkshopModSearchWebsiteScarper(search_query)

        # Create Discord embed for better formatting
        embed = discord.Embed(
            title="Mod Details",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )

        # Create the view with buttons
        view = View(timeout=None)

        # Create buttons
        for idx, mod in enumerate(workshop_scarper):
            add_button = Button(
                style=discord.ButtonStyle.blurple,
                label="{}. {}".format(idx + 1, mod["name"]),
                custom_id="add_mod:{}:{}:{}".format(
                    mod["id"], mod["name"], mod["version"]
                ),
                row=idx,
            )

            is_installed = mod["id"] in self.server_config.game.searchable_mods
            if is_installed:
                add_button.style = discord.ButtonStyle.grey
                add_button.label += " (Installed)"
                add_button.disabled = True

            view.add_item(add_button)

        if workshop_scarper:
            embed.description = "Search results for **{}**:".format(search_query)
        else:
            embed.discription = "No mods found for **{}**.".format(search_query)
            embed.color = discord.Color.red()

        return embed, view

    async def create_or_update_mod_message(self, mod_id):
        if not self.channel:
            self.channel = get_channel(self.bot, self.channel_id)

        # Get the message content
        embed, view = self.make_mod_message(mod_id)

        # Fetch the message
        message_key = "mod_{}_status_message_id".format(mod_id)
        if message_key in self.messages_cache:
            message = self.messages_cache[message_key]
            await message.edit(content=None, embed=embed, view=view)
        else:
            message = await self.channel.send(embed=embed, view=view)
            self.messages_cache[message_key] = message

    @tasks.loop(minutes=1)
    async def create_or_update_mod_messages(self):
        if self.mod_idx == -1:
            # Clear all previous messages
            await self.clear()

        self.mod_idx += 1
        if self.mod_idx >= len(self.server_config.game.mods):
            self.mod_idx = 0

        # Create or update the message for the chosen mod
        mod = self.server_config.game.mods[self.mod_idx]
        mod_id = mod["modId"]
        await self.create_or_update_mod_message(mod_id)

    async def create_mod_search_message(self, search_query):
        if not self.channel:
            self.channel = get_channel(self.bot, self.channel_id)

        embed, view = self.make_mod_search_message(search_query)

        await self.channel.send(embed=embed, view=view)

    async def handle_message(self, message):
        search_query = message.content.strip()
        await message.delete()
        await self.create_mod_search_message(search_query)

    async def handle_interaction(self, interaction):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        # Check if the interaction is from a button
        if interaction.type == InteractionType.component:
            if interaction.data["component_type"] == 2:
                custom_id = interaction.data["custom_id"].split(":")
                message_type = custom_id[0]
                mod_id = custom_id[1]

                if message_type == "add_mod":
                    mod_name = custom_id[2]
                    mod_version = custom_id[3]
                    add_mod_to_serverconfig(
                        config.SERVERCONFIG_PATH, mod_id, mod_name, mod_version
                    )

                    await interaction.message.delete()
                    await self.create_or_update_mod_message(mod_id)

                elif message_type == "update_mod":
                    new_version = custom_id[2]
                    update_mod_version_in_serverconfig(
                        config.SERVERCONFIG_PATH, mod_id, new_version
                    )

                    await self.create_or_update_mod_message(mod_id)

                elif message_type == "check_mod":
                    await self.create_or_update_mod_message(mod_id)

                elif message_type == "remove_mod":
                    remove_mod_from_serverconfig(config.SERVERCONFIG_PATH, mod_id)

                    await self.delete_mod_message(mod_id)

                else:
                    await interaction.response.send_message(
                        "Unknown command.", ephemeral=True
                    )

    async def delete_mod_message(self, mod_id):
        if not self.channel:
            return False

        message_key = "mod_{}_status_message_id".format(mod_id)
        if message_key in self.messages_cache:
            message = self.messages_cache[message_key]
            self.messages_cache.pop(message_key)
            await message.delete()

    async def clear(self):
        if not self.channel:
            self.channel = get_channel(self.bot, self.channel_id)

        await self.channel.purge(limit=None)
        self.messages_cache.clear()
