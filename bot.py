import sys
import signal
import subprocess
import asyncio

import discord
from discord.ext import commands

import config
from utils.cache import ACTIVE_PLAYERS_BOHEMIA_ID_CACHE
from utils.utils import restart_gameserver2
from utils.database_managers import (
    users_dbm,
    role_logs_dbm,
    misconduct_logs_dbm,
)
from utils.active_messages import (
    create_or_update_server_utilization_status_message,
    create_or_update_teams_members_status_message,
    create_or_update_active_players_on_gameserver_status_message,
    ActiveModsActiveMessages,
)
from utils.file_watchers import ServerAdminToolsStatsFileWatcher

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
intents.reactions = True
intents.presences = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Channel IDs
testing_channel_id = 1133538801956962414
join_us_channe_id = 1353325596310241341
stats_channel_id = 1352022770120265828
roles_channel_id = 1195682437628432495
server_status_channel_id = 1366455194728136804

# Active Messages
active_mods_am = ActiveModsActiveMessages(
    bot, testing_channel_id, config.SERVERCONFIG_PATH
)

# File Watchers
server_stats_file_watcher = ServerAdminToolsStatsFileWatcher(config.SERVERSTATS_PATH)


# Slash Command: /ping
@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong", ephemeral=True)


# Slash Command: /register
@bot.tree.command(name="register", description="Register yourself in the database")
async def register(interaction: discord.Interaction):
    user = interaction.user
    users_dbm.create(user.id, user.name, user.display_name)
    role_logs_dbm.create(
        user.id, user.id, "Unassigned", "User registered himself/herself"
    )
    await interaction.response.send_message(
        f"Registered {user.name} in the database.", ephemeral=True
    )


# Slash Command: /register_user
@bot.tree.command(name="register_user", description="Register a user in the database")
@discord.app_commands.describe(user="The user to change team for")
async def register_user(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    users_dbm.create(user.id, user.name, user.display_name)
    role_logs_dbm.create(
        interaction.user.id, user.id, "Unassigned", "User was registered by admin"
    )
    await interaction.response.send_message(
        f"Registered {user.name} in the database.", ephemeral=True
    )


# Slash Command: /privacy
@bot.tree.command(name="privacy", description="Show the privacy policy")
async def privacy(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Privacy Policy for Talon Bot",
        description='Last Updated: May 6, 2025\n\nThis Privacy Policy explains what information Talon Bot ("we," "our," or "us") collects, how we use and store this information, and your rights regarding this information. By joining our discord server, you consent to the data practices described in this policy.',
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="1. Information We Collect",
        value="We collect and store the following information:\n\n- Discord ID: A unique identifier assigned to your Discord account.\n- Discord Username: Your current username on Discord.\n- Discord Display Name: Your display name as shown on our server.\n- Bohemia ID: Your unique identifier for Bohemia Interactive games which can be used to uniquely identify individuals across platforms.",
        inline=False,
    )

    embed.add_field(
        name="2. How We Use Your Information",
        value="We collect this information for the following purposes:\n\n- To identify you consistently across username or display name changes.\n- To manage community membership and participation.\n- To apply in-game rewards and punishments through the Bohemia ID system.\n- To maintain server security and enforce community guidelines.",
        inline=False,
    )

    embed.add_field(
        name="3. Data Retention",
        value="We retain your information for as long as you remain a member of our community or until you request deletion. Please note that requesting data deletion will result in removal from our Discord server, as explained in Section 5.",
        inline=False,
    )

    embed.add_field(
        name="4. Data Sharing",
        value="We do not sell or share your information with third parties except as necessary to:\n\n- Fulfil the bot's core functionality (applying in-game rewards/punishments).\n- Comply with legal obligations.\n- Enforce our server rules and terms.",
        inline=False,
    )

    embed.add_field(
        name="5. Your Rights and Choices",
        value="You may request deletion of your data at any time by raising a helpdesk ticket within our Discord server. Please note that data deletion will result in being banned from our Discord server, and by violating our server rules be blacklisted entirely, as we cannot maintain our community without keeping track of required information. We aim to erase your information within one month of the request date.",
        inline=False,
    )

    embed.add_field(
        name="6. Changes to This Policy",
        value="We may update this Privacy Policy periodically. We will notify users of any significant changes by posting an announcement in our Discord server.",
        inline=False,
    )

    embed.add_field(
        name="7. Contact Information",
        value="If you have questions about this Privacy Policy, please contact Red-Sep, J-Mac, HZN or May-Day.",
        inline=False,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# Slash Command: /delete_user
@bot.tree.command(name="delete_user", description="Delete a user from the database")
@discord.app_commands.describe(user="The user to delete")
async def delete_user(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    users_dbm.delete(user.id)
    role_logs_dbm.mark_as_deleted_by_instigator_discord_id(user.id)
    role_logs_dbm.mark_as_deleted_by_target_discord_id(user.id)
    misconduct_logs_dbm.mark_as_deleted_by_instigator_discord_id(user.id)
    misconduct_logs_dbm.mark_as_deleted_by_target_discord_id(user.id)
    misconduct_logs_dbm.mark_as_deleted_by_victim_discord_id(user.id)
    await interaction.response.send_message(
        f"Deleted {user.name} from the database.", ephemeral=True
    )


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

    old_team = users_dbm.read_team(user.id)
    old_role = interaction.guild.get_role(config.TEAMS[old_team])
    new_role = interaction.guild.get_role(config.TEAMS[new_team])

    if old_team == "Red Talon":
        await interaction.response.send_message(
            "User is a Red Talon. User can't be demoted!", ephemeral=True
        )
        return

    await user.remove_roles(old_role)
    await user.add_roles(new_role)

    users_dbm.update_team(user.id, new_team)
    users_dbm.reset_joined(user.id)
    role_logs_dbm.create(
        interaction.user.id, user.id, new_team, "User was assigned a new team by admin"
    )
    await create_or_update_teams_members_status_message(
        bot, stats_channel_id, users_dbm
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
    for entry in role_logs_dbm.read_by_target_discord_id(user.id):
        user_a_discord_displayname = users_dbm.read_discord_displayname(entry[1])
        user_b_discord_displayname = users_dbm.read_discord_displayname(entry[2])
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
    misconduct_logs_dbm.create(
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
    for entry in misconduct_logs_dbm.read_by_target_discord_id(user.id):
        user_a_discord_displayname = users_dbm.read_discord_displayname(entry[1])
        user_b_discord_displayname = users_dbm.read_discord_displayname(entry[2])
        user_c_discord_displayname = (
            users_dbm.read_discord_displayname(entry[3])
            if entry[3] is not None
            else "N/A"
        )
        message += f"Initiator: {user_a_discord_displayname}\nAccused: {user_b_discord_displayname}\nVictim: {user_c_discord_displayname}\nCategory: {entry[4]}\nType: {entry[5]}\nDetails: {entry[6]}\nSeverity: {entry[7]}\nTimestamp: {entry[8]}\n\n"

    await interaction.response.send_message(message)


# Slash Command: /restart_gameserver
@bot.tree.command(name="restart_gameserver", description="Restart the game server")
async def restart_gameserver(interaction: discord.Interaction):
    if interaction.user.id not in config.ADMIN_IDS:
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return

    try:
        restart_gameserver2()
        await interaction.response.send_message(
            "Game server is restarting...", ephemeral=True
        )
    except subprocess.CalledProcessError as e:
        await interaction.response.send_message(
            f"Failed to restart the game server: {e}", ephemeral=True
        )


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

    users_dbm.update_bohemia_id(user.id, in_game_name)
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
    if users_dbm.read(user.id):
        users_dbm.update_status(user.id, "Active")
        users_dbm.reset_joined(user.id)
        role_logs_dbm.create(
            user.id,
            user.id,
            "Unassigned",
            "User has rejoined the server",
        )
        print(f"{user.display_name} is already registered.")
    # register the user in the database
    else:
        users_dbm.create(user.id, user.name, user.display_name)
        role_logs_dbm.create(
            user.id,
            user.id,
            "Unassigned",
            "User has joined the server",
        )
        print(f"Registered {user.display_name} in the database.")

    # Update the status message
    await create_or_update_teams_members_status_message(
        bot, stats_channel_id, users_dbm
    )


# Leave Tracking
@bot.event
async def on_member_remove(user):
    users_dbm.update_status(user.id, "Inactive")
    users_dbm.update_team(user.id, "Unassigned")
    role_logs_dbm.create(
        user.id,
        user.id,
        "Unassigned",
        "User has left the server",
    )
    await create_or_update_teams_members_status_message(
        bot, stats_channel_id, users_dbm
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
                bot, stats_channel_id, users_dbm
            )
        # Update Status Message
        if interaction.data["custom_id"] == "refresh_server_utilization_status_message":
            # Acknowledge the button press
            await interaction.response.defer(ephemeral=True)

            # Call the update function
            await create_or_update_server_utilization_status_message(
                bot, stats_channel_id
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
        channel_id == roles_channel_id
        and message_id == 1366811865094553691
        and emoji.name == "🟩"
    ):
        old_team = users_dbm.read_team(user_id)
        role = guild.get_role(1350899518773919908)
        await member.add_roles(role)

        if old_team == "Unassigned":
            users_dbm.update_team(user_id, "Green Team")
            users_dbm.reset_joined(user_id)
        role_logs_dbm.create(
            user_id,
            user_id,
            "Green Team",
            "User joined himself/herself as a Green Team member",
        )

        await create_or_update_teams_members_status_message(
            bot, stats_channel_id, users_dbm
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
        bot, stats_channel_id, users_dbm
    )

    # Set up self-looping active messages
    create_or_update_active_players_on_gameserver_status_message.start(
        bot=bot,
        channel_id=server_status_channel_id,
        server_stats=server_stats_file_watcher,
    )
    create_or_update_server_utilization_status_message.start(
        bot=bot, channel_id=stats_channel_id
    )

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        bot.loop.add_signal_handler(sig, lambda: bot.loop.create_task(shutdown()))


# Shutdown
async def shutdown():
    print("Shutdown initiated - removing messages")
    await active_mods_am.shutdown()
    await bot.close()
    sys.exit(0)


# Load all cogs
async def main():
    # Load cogs here
    await bot.load_extension("cogs.serverconfig")
    await bot.load_extension("cogs.mos")

    # Start the bot
    await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
