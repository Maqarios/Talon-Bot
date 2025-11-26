import datetime
import re
import time

import config
import discord
from discord import InteractionType
from discord.ext import tasks
from discord.ui import Button, View
from utils.cache import ACTIVE_PLAYERS_BOHEMIA_ID_CACHE
from utils.utils import (
    add_mod_to_serverconfig,
    format_mos,
    format_time_elapsed,
    get_active_messages_id,
    get_channel,
    get_server_utilization,
    is_port_listening,
    remove_mod_from_serverconfig,
    set_active_messages_id,
    update_mod_version_in_serverconfig,
)
from utils.website_scrapers import (
    WorkshopModPageWebsiteScraper,
    WorkshopModSearchWebsiteScraper,
)


async def create_empty_message(channel, initial_message="Empty Message"):
    message = await channel.send(initial_message)
    return message


@tasks.loop(seconds=30)
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

    # Get data from database
    users = user_dbm.get_users_for_active_message()

    # Group users by team
    teams = {team: [] for team in config.TEAMS}
    for user_id, user_status, user_team, user_joined in users:
        if user_status == "Active" and user_team in config.TEAMS:
            teams[user_team].append((user_id, user_joined))

    # Add each team as a field in the embed
    embed_list = []
    for team_name, members in teams.items():

        if team_name in ["Unassigned", "Green Team", "Red Talon"]:
            continue  # Skip Unassigned and Green Team

        # Create Discord embed for better formatting
        embed_title = team_name
        embed_color = discord.Color(0xFFFFFE)

        if team_name == "Chalk Team":
            embed_color = discord.Color.gold()
        elif team_name == "Red Section":
            embed_color = discord.Color(0xDC143C)
        elif team_name == "Grey Section":
            embed_color = discord.Color.light_grey()
        elif team_name == "Black Section":
            embed_color = discord.Color(0x000001)

        name_list = ""
        mos_list = ""
        joined_list = ""
        for idx, (member_id, joined) in enumerate(members):
            user = bot.get_user(member_id)
            member = await bot.guilds[0].fetch_member(member_id)

            display_name = user.display_name
            user_roles = member.roles

            if len(display_name) > 23:
                name_list += f"{idx + 1}• {display_name[:23]}...\n"
            else:
                name_list += f"{idx + 1}• {display_name}\n"

            if len(format_mos(user_roles, config.MOS_ROLES)) > 20:
                mos_list += f"{format_mos(user_roles, config.MOS_ROLES)[:20]}...\n"
            else:
                mos_list += f"{format_mos(user_roles, config.MOS_ROLES)[:20]}\n"

            joined_list += f"{format_time_elapsed(joined)}\n"

        # If no members, set to "No members"
        if not members:
            name_list = "N/A"
            mos_list = "N/A"
            joined_list = "N/A"

        name_list += "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
        mos_list += "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
        joined_list += "⠀⠀⠀⠀⠀⠀⠀⠀"

        # Create embed and add fields to it
        embed = discord.Embed(
            title=embed_title,
            color=embed_color,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(name="Name", value=name_list, inline=True)
        embed.add_field(name="MOS", value=mos_list, inline=True)
        embed.add_field(name="Last Seen", value=joined_list, inline=True)

        # Add embed to the embed list
        embed_list.append(embed)

    # Edit the message with the new content
    try:
        await message.edit(content=None, embeds=embed_list, view=view)
    except discord.NotFound:
        time.sleep(config.SLEEP_TIME)
        create_or_update_teams_members_status_message(bot, channel_id, user_dbm)
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    return True


@tasks.loop(seconds=30)
async def create_or_update_active_players_on_arma_reforger_server_status_message(
    entries,
):
    await create_or_update_active_players_on_arma_reforger_server_status_message_util(
        *entries[0]
    )
    await create_or_update_active_players_on_arma_reforger_server_status_message_util(
        *entries[1]
    )
    await create_or_update_active_players_on_arma_reforger_server_status_message_util(
        *entries[2]
    )


async def create_or_update_active_players_on_arma_reforger_server_status_message_util(
    bot,
    channel_id,
    server_number,
    server_stats,
    server_config,
    users_dbm,
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
            f"active_players_on_arma_reforger_server_status_message_id_{server_number}",
        )
        message = await channel.fetch_message(message_id)
    except (FileNotFoundError, KeyError, discord.NotFound) as e:
        message = await create_empty_message(
            channel, "Creating a new message for active players status."
        )
        set_active_messages_id(
            config.ACTIVEMESSAGESIDS_PATH,
            f"active_players_on_arma_reforger_server_status_message_id_{server_number}",
            message.id,
        )
    except discord.Forbidden:
        print(
            f"Permission denied. Contact the server administrator to check permissions for channel {channel_id}."
        )
        return False

    # Create Discord embed for better formatting
    embed = discord.Embed(
        title=f"Server {server_number}: Online",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now(),
    )

    # Get gameserver online status
    gameserver_status = is_port_listening(server_config.bindPort)

    if not gameserver_status:
        # await channel.edit(name=f"⏳│𝐒𝐞𝐫𝐯𝐞𝐫-𝐒𝐭𝐚𝐭𝐮𝐬-〔Offline〕")
        embed.title = f"Server {server_number}: Offline"
        embed.color = discord.Color.red()
    else:
        # await channel.edit(
        #     name=f"⏳│𝐒𝐞𝐫𝐯𝐞𝐫-𝐒𝐭𝐚𝐭𝐮𝐬-〔{server_stats.players}／{server_config.game.maxPlayers}〕"
        # )

        # Define the field to be added

        # Players list field
        field = {"name": "", "value": "", "inline": False}

        if server_stats.players == -1:
            embed.color = discord.Color.red()
            field["name"] = "Something went wrong. Contact the server administrator."
        if server_stats.players == 0:
            embed.color = discord.Color.yellow()
            field["name"] = (
                f"Players ( {server_stats.players} / {server_config.game.maxPlayers} )"
            )
        else:
            field["name"] = (
                f"Operatives ( {server_stats.players} / {server_config.game.maxPlayers} )"
            )
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

                if ACTIVE_PLAYERS_BOHEMIA_ID_CACHE.is_known_player(player_bohemia_id):
                    player_discord_id = users_dbm.read_by_bohemia_id(player_bohemia_id)[
                        0
                    ]
                    users_dbm.reset_joined(player_discord_id)

        embed.add_field(**field)

        # Server details field
        embed.add_field(
            name="Server Details",
            value=(
                f"• **Name:** {server_config.game.name}\n"
                f"• **Scenario:** {(' ').join(re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z]*', server_config.game.scenarioId.split('/')[-1].split('.')[0]))}\n"
                f"• **Password:** {server_config.game.password}\n"
                f"• **IP:** {server_config.publicAddress}\n"
                f"• **Port:** {server_config.publicPort}\n"
                f"• **Uptime:** {datetime.timedelta(seconds=server_stats.uptime_seconds)}\n"
            ),
            inline=False,
        )

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
    def __init__(self, bot, channel_id, server_config, server_config_path):
        self.bot = bot
        self.channel_id = channel_id
        self.server_config = server_config
        self.server_config_path = server_config_path

        self.channel = None
        self.messages_cache = {}
        self.mod_idx = -1  # Used to track the index of the mod being processed

    def make_mod_message(self, mod_id):
        # Get mod details
        workshop_scraper = WorkshopModPageWebsiteScraper(mod_id)
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
            custom_id="update_mod:{}:{}".format(mod_id, workshop_scraper.version),
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
            != workshop_scraper.version
        ):
            embed.title = "{} (Update Available)".format(workshop_scraper.name)
            embed.color = discord.Color.blue()
            embed.description = "**Version: {} ⟶ {}**\n[Workshop Link]({})".format(
                self.server_config.game.searchable_mods[mod_id]["version"],
                workshop_scraper.version,
                config.WORKSHOP_MOD_PAGE_URL + mod_id,
            )

            view.add_item(update_button)
            view.add_item(check_button)
            view.add_item(delete_button)

        else:
            embed.title = "{}".format(workshop_scraper.name)
            embed.color = discord.Color.green()
            embed.description = "**Version: {}**\n[Workshop Link]({})".format(
                workshop_scraper.version, config.WORKSHOP_MOD_PAGE_URL + mod_id
            )

            view.add_item(check_button)
            view.add_item(delete_button)

        if workshop_scraper.dependencies:
            dependency_content = ""

            for (
                dependency_id,
                dependency_details,
            ) in workshop_scraper.dependencies.items():
                dependency_content += "{}\n".format(dependency_details["name"])

            embed.add_field(
                name="Dependencies",
                value=dependency_content,
                inline=False,
            )

        return embed, view

    def make_mod_search_message(self, search_query):
        # Get mod details
        workshop_scraper = WorkshopModSearchWebsiteScraper(search_query)

        # Create Discord embed for better formatting
        embed = discord.Embed(
            title="Mod Details",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(),
        )

        # Create the view with buttons
        view = View(timeout=None)

        # Create buttons
        for idx, mod in enumerate(workshop_scraper):
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

        if workshop_scraper:
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

        try:
            message = self.messages_cache[message_key]
            await message.edit(content=None, embed=embed, view=view)
        except (KeyError, discord.NotFound) as e:
            message = await self.channel.send(embed=embed, view=view)
            self.messages_cache[message_key] = message

    @tasks.loop(minutes=1)
    async def create_or_update_mod_messages(self):
        if self.mod_idx == -1:
            # Clear all previous messages
            await self.clear()

        if len(self.server_config.game.mods) == 0:
            return  # No mods to process

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
                        self.server_config_path, mod_id, mod_name, mod_version
                    )

                    await interaction.message.delete()
                    await self.create_or_update_mod_message(mod_id)

                elif message_type == "update_mod":
                    new_version = custom_id[2]
                    update_mod_version_in_serverconfig(
                        self.server_config_path, mod_id, new_version
                    )

                    await self.create_or_update_mod_message(mod_id)

                elif message_type == "check_mod":
                    await self.create_or_update_mod_message(mod_id)

                elif message_type == "remove_mod":
                    remove_mod_from_serverconfig(self.server_config_path, mod_id)

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
