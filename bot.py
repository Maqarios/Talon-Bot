import sys
import signal
import asyncio

import discord
from discord.ext import commands

import config
from utils.cache import ACTIVE_PLAYERS_BOHEMIA_ID_CACHE
from utils.database_managers import (
    USERS_DBM,
    ROLE_LOGS_DBM,
    MISCONDUCT_LOGS_DBM,
)
from utils.active_messages import (
    create_or_update_server_utilization_status_message,
    create_or_update_teams_members_status_message,
    create_or_update_active_players_on_gameserver_status_message,
)
from utils.file_watchers import ServerAdminToolsStatsFileWatcher

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
intents.reactions = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

# File Watchers
server_stats_file_watcher = ServerAdminToolsStatsFileWatcher(config.SERVERSTATS_PATH)


# Slash Command: /change_user_team
@bot.tree.command(name="change_user_team", description="Change a user's team")
@discord.app_commands.describe(
    user="The user to change team for", new_team="The new team to assign"
)
@discord.app_commands.choices(
    new_team=[
        discord.app_commands.Choice(name=team, value=team)
        for team in config.TEAMS.keys()
    ]
)
async def change_user_team(
    interaction: discord.Interaction,
    user: discord.User,
    new_team: str,
):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    old_team = USERS_DBM.read_team(user.id)
    old_role = interaction.guild.get_role(config.TEAMS[old_team])
    new_role = interaction.guild.get_role(config.TEAMS[new_team])

    if old_team == "Red Talon":
        await interaction.response.send_message(
            "User is a Red Talon. User can't be demoted!", ephemeral=True
        )
        return

    await user.remove_roles(old_role)
    await user.add_roles(new_role)

    USERS_DBM.update_team(user.id, new_team)
    USERS_DBM.reset_joined(user.id)
    ROLE_LOGS_DBM.create(
        interaction.user.id, user.id, new_team, "User was assigned a new team by admin"
    )
    await create_or_update_teams_members_status_message(
        bot, config.CHANNEL_IDS["Stats"], USERS_DBM
    )
    await interaction.response.send_message(
        f"Updated {user.name}'s team to {new_team}.", ephemeral=True
    )


# Slash Command: /show_user_team_logs
@bot.tree.command(name="show_user_team_logs", description="Show a user's team logs")
@discord.app_commands.describe(user="The user to show logs for")
async def show_user_team_logs(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    message = ""
    for entry in ROLE_LOGS_DBM.read_by_target_discord_id(user.id):
        user_a_discord_displayname = USERS_DBM.read_discord_displayname(entry[1])
        user_b_discord_displayname = USERS_DBM.read_discord_displayname(entry[2])
        message += f"User A: {user_a_discord_displayname}, User B: {user_b_discord_displayname}, Team: {entry[3]}, Details: {entry[4]}, Timestamp: {entry[5]}\n"

    await interaction.response.send_message(message)


# Slash Command: /add_misconduct
@bot.tree.command(
    name="add_misconduct", description="Add a misconduct to a user in the database"
)
@discord.app_commands.describe(
    target_user="The user to add misconduct for",
    category="The category of the misconduct",
    type="The type of the misconduct",
    details="Details about the misconduct",
    severity="Severity of the misconduct (0-2)",
    victim_user="The user who was affected by the misconduct (optional)",
)
@discord.app_commands.choices(
    category=[
        discord.app_commands.Choice(name=cat, value=cat)
        for cat in config.MISCONDUCT_CATEGORIES.keys()
    ],
    type=[
        discord.app_commands.Choice(name=cat, value=cat)
        for cat in [
            item
            for sublist in config.MISCONDUCT_CATEGORIES.values()
            for item in sublist
        ]
    ],
    severity=[
        discord.app_commands.Choice(name="Green", value=0),
        discord.app_commands.Choice(name="Yellow", value=1),
        discord.app_commands.Choice(name="Red", value=2),
    ],
)
async def add_misconduct(
    interaction: discord.Interaction,
    target_user: discord.User,
    category: str,
    type: str,
    details: str,
    severity: int,
    victim_user: discord.User = None,
):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    victim_id = victim_user.id if victim_user else None
    MISCONDUCT_LOGS_DBM.create(
        interaction.user.id,
        target_user.id,
        victim_id,
        category,
        type,
        details,
        severity,
    )

    await interaction.response.send_message(
        f"Added misconduct for {target_user.name} in category {category}, type {type}, details: {details}, severity: {severity}.",
        ephemeral=True,
    )


# Slash Command: /show_misconducts
@bot.tree.command(name="show_misconducts", description="Show a user's misconduct logs")
@discord.app_commands.describe(user="The user to show logs for")
async def show_misconducts(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    message = ""
    for entry in MISCONDUCT_LOGS_DBM.read_by_target_discord_id(user.id):
        user_a_discord_displayname = USERS_DBM.read_discord_displayname(entry[1])
        user_b_discord_displayname = USERS_DBM.read_discord_displayname(entry[2])
        user_c_discord_displayname = (
            USERS_DBM.read_discord_displayname(entry[3])
            if entry[3] is not None
            else "N/A"
        )
        message += f"Initiator: {user_a_discord_displayname}\nAccused: {user_b_discord_displayname}\nVictim: {user_c_discord_displayname}\nCategory: {entry[4]}\nType: {entry[5]}\nDetails: {entry[6]}\nSeverity: {entry[7]}\nTimestamp: {entry[8]}\n\n"

    await interaction.response.send_message(message)


# Slash Command: /link_user_bohemia_id
@bot.tree.command(
    name="link_user_bohemia_id",
    description="Link a player bohemia id to the users database",
)
@discord.app_commands.describe(
    user="The user to link bohemia id for", in_game_name="The bohemia id to link"
)
async def link_user_bohemia_id(
    interaction: discord.Interaction, user: discord.User, in_game_name: str
):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    USERS_DBM.update_bohemia_id(user.id, in_game_name)
    ACTIVE_PLAYERS_BOHEMIA_ID_CACHE.add_known_player(user.id, in_game_name)
    ACTIVE_PLAYERS_BOHEMIA_ID_CACHE.remove_unknown_player(in_game_name)
    await interaction.response.send_message(
        f"Added {in_game_name} to {user.name}'s bohemia id.", ephemeral=True
    )


@link_user_bohemia_id.autocomplete("in_game_name")
async def in_game_name_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[discord.app_commands.Choice[str]]:
    unknown_players = ACTIVE_PLAYERS_BOHEMIA_ID_CACHE.get_unknown_players()

    return [
        discord.app_commands.Choice(name=player_name, value=str(player_bohemia_id))
        for player_bohemia_id, player_name in unknown_players.items()
        if current.lower() in player_name.lower()
    ][:25]


# Join Registering
@bot.event
async def on_member_join(user):
    # Check if the member is already registered
    if USERS_DBM.read(user.id):
        USERS_DBM.update_status(user.id, "Active")
        USERS_DBM.reset_joined(user.id)
        ROLE_LOGS_DBM.create(
            user.id,
            user.id,
            "Unassigned",
            "User has rejoined the server",
        )
        print(f"{user.display_name} is already registered.")
    # register the user in the database
    else:
        USERS_DBM.create(user.id, user.name, user.display_name)
        ROLE_LOGS_DBM.create(
            user.id,
            user.id,
            "Unassigned",
            "User has joined the server",
        )
        print(f"Registered {user.display_name} in the database.")

    # Update the status message
    await create_or_update_teams_members_status_message(
        bot, config.CHANNEL_IDS["Stats"], USERS_DBM
    )


# Leave Tracking
@bot.event
async def on_member_remove(user):
    USERS_DBM.update_status(user.id, "Inactive")
    USERS_DBM.update_team(user.id, "Unassigned")
    ROLE_LOGS_DBM.create(
        user.id,
        user.id,
        "Unassigned",
        "User has left the server",
    )
    await create_or_update_teams_members_status_message(
        bot, config.CHANNEL_IDS["Stats"], USERS_DBM
    )


# Interaction Tracking
@bot.event
async def on_interaction(interaction):
    if interaction.data and "custom_id" in interaction.data:
        # Update Status Message
        if interaction.data["custom_id"] == "refresh_teams_members_status_message":
            # Acknowledge the button press
            await interaction.response.defer(ephemeral=True)

            # Call the update function
            await create_or_update_teams_members_status_message(
                bot, config.CHANNEL_IDS["Stats"], USERS_DBM
            )
        # Update Status Message
        if interaction.data["custom_id"] == "refresh_server_utilization_status_message":
            # Acknowledge the button press
            await interaction.response.defer(ephemeral=True)

            # Call the update function
            await create_or_update_server_utilization_status_message(
                bot, config.CHANNEL_IDS["Stats"]
            )


# Reaction Tracking
@bot.event
async def on_raw_reaction_add(payload):
    # Get information from the payload
    channel_id = payload.channel_id
    message_id = payload.message_id
    user_id = payload.user_id
    emoji = payload.emoji
    member = payload.member
    guild = member.guild

    # Green Team Join
    if (
        channel_id == config.CHANNEL_IDS["Rules"]
        and message_id == 1366811865094553691
        and emoji.name == "🟩"
    ):
        old_team = USERS_DBM.read_team(user_id)
        role = guild.get_role(1350899518773919908)
        await member.add_roles(role)

        if old_team == "Unassigned":
            USERS_DBM.update_team(user_id, "Green Team")
            USERS_DBM.reset_joined(user_id)
        ROLE_LOGS_DBM.create(
            user_id,
            user_id,
            "Green Team",
            "User joined himself/herself as a Green Team member",
        )

        await create_or_update_teams_members_status_message(
            bot, config.CHANNEL_IDS["Stats"], USERS_DBM
        )


# Bot ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        for command in synced:
            print(f"✅ Synced slash command: {command.name}")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

    # Start file watcher
    server_stats_file_watcher.start()

    # Set up active messages
    await create_or_update_teams_members_status_message(
        bot, config.CHANNEL_IDS["Stats"], USERS_DBM
    )

    # Set up self-looping active messages
    create_or_update_active_players_on_gameserver_status_message.start(
        bot=bot,
        channel_id=config.CHANNEL_IDS["Server Status"],
        server_stats=server_stats_file_watcher,
    )
    create_or_update_server_utilization_status_message.start(
        bot=bot, channel_id=config.CHANNEL_IDS["Stats"]
    )

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        bot.loop.add_signal_handler(sig, lambda: bot.loop.create_task(shutdown()))


# Shutdown
async def shutdown():
    print("Shutdown initiated")
    await bot.close()
    sys.exit(0)


# Load all cogs
async def main():
    # Load cogs here
    await bot.load_extension("cogs.user")
    await bot.load_extension("cogs.misc")
    await bot.load_extension("cogs.serverconfig")
    await bot.load_extension("cogs.mos")

    # Start the bot
    await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
