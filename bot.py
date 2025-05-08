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
from utils.file_watchers import (
    ServerAdminToolsStatsFileWatcher,
    ServerConfigFileWatcher,
)

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
intents.reactions = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

# File Watchers
server_stats_file_watcher = ServerAdminToolsStatsFileWatcher(config.SERVERSTATS_PATH)
server_config_file_watcher = ServerConfigFileWatcher(config.SERVERCONFIG_PATH)


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
    server_config_file_watcher.start()

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
