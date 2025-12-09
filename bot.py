import asyncio
import signal
import sys

import config
import discord
from discord.ext import commands
from utils import configure_logging, get_logger
from utils.active_messages import (
    ModsActiveMessages,
    create_or_update_active_players_on_arma_reforger_server_status_message,
    create_or_update_server_utilization_status_message,
    create_or_update_teams_members_status_message,
)
from utils.database_managers import ROLE_LOGS_DBM, USERS_DBM
from utils.file_watchers import (
    ServerAdminToolsStatsFileWatcher,
    ServerConfigFileWatcher,
)
from utils.misc import LoadoutSnapshotter
from utils.utils import (
    add_player_to_playersgroups,
    remove_player_from_playersgroups,
    send_embed,
)


class TalonBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # File Watchers
        self.server_config_file_watcher_1 = ServerConfigFileWatcher(
            config.GET_ARMAR_SERVERCONFIG_FILE_PATH(1)
        )
        self.server_config_file_watcher_2 = ServerConfigFileWatcher(
            config.GET_ARMAR_SERVERCONFIG_FILE_PATH(2)
        )
        self.server_config_file_watcher_3 = ServerConfigFileWatcher(
            config.GET_ARMAR_SERVERCONFIG_FILE_PATH(3)
        )
        self.server_stats_file_watcher_1 = ServerAdminToolsStatsFileWatcher(
            config.GET_ARMAR_SERVERSTATS_FILE_PATH(1)
        )
        self.server_stats_file_watcher_2 = ServerAdminToolsStatsFileWatcher(
            config.GET_ARMAR_SERVERSTATS_FILE_PATH(2)
        )
        self.server_stats_file_watcher_3 = ServerAdminToolsStatsFileWatcher(
            config.GET_ARMAR_SERVERSTATS_FILE_PATH(3)
        )

        # Snapshotters
        self.loadout_snapshotter_1 = LoadoutSnapshotter(
            monitor_dir=config.GET_ARMAR_BLE_DIR_PATH(1), max_snapshots=6
        )
        self.loadout_snapshotter_2 = LoadoutSnapshotter(
            monitor_dir=config.GET_ARMAR_BLE_DIR_PATH(2), max_snapshots=6
        )
        self.loadout_snapshotter_3 = LoadoutSnapshotter(
            monitor_dir=config.GET_ARMAR_BLE_DIR_PATH(3), max_snapshots=6
        )

        # Active Messages
        self.mods_active_messages_1 = ModsActiveMessages(
            self,
            config.CHANNEL_IDS["Mods-Server-1"],
            self.server_config_file_watcher_1,
            config.GET_ARMAR_SERVERCONFIG_FILE_PATH(1),
        )
        self.mods_active_messages_2 = ModsActiveMessages(
            self,
            config.CHANNEL_IDS["Mods-Server-2"],
            self.server_config_file_watcher_2,
            config.GET_ARMAR_SERVERCONFIG_FILE_PATH(2),
        )
        self.mods_active_messages_3 = ModsActiveMessages(
            self,
            config.CHANNEL_IDS["Mods-Server-3"],
            self.server_config_file_watcher_3,
            config.GET_ARMAR_SERVERCONFIG_FILE_PATH(3),
        )

    async def setup_hook(self):
        # Load cogs here
        await self.load_extension("cogs.user")
        await self.load_extension("cogs.misc")
        await self.load_extension("cogs.serverconfig")
        await self.load_extension("cogs.mos")
        await self.load_extension("cogs.log")

        # Start file watchers
        self.server_config_file_watcher_1.start()
        self.server_config_file_watcher_2.start()
        self.server_config_file_watcher_3.start()
        self.server_stats_file_watcher_1.start()
        self.server_stats_file_watcher_2.start()
        self.server_stats_file_watcher_3.start()

        # Start snapshotters
        self.loadout_snapshotter_1.start()
        self.loadout_snapshotter_2.start()
        self.loadout_snapshotter_3.start()

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            for command in synced:
                log.info(f"✅ Synced slash command: {command.name}")
        except Exception as e:
            log.error(f"❌ Failed to sync slash commands: {e}")

        # Set up signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            bot.loop.add_signal_handler(
                sig, lambda: bot.loop.create_task(self.shutdown())
            )

    async def on_ready(self):
        log.info(f"✅ Logged in as {bot.user} (ID: {self.user.id})")

        # Set up active messages
        await create_or_update_teams_members_status_message(
            bot, config.CHANNEL_IDS["Stats"], USERS_DBM
        )

        # Set up self-looping active messages
        armar_active_players = []
        armar_active_players.append(
            (
                bot,
                config.CHANNEL_IDS["Server Status"],
                1,
                self.server_stats_file_watcher_1,
                self.server_config_file_watcher_1,
                USERS_DBM,
            )
        )
        armar_active_players.append(
            (
                bot,
                config.CHANNEL_IDS["Server Status"],
                2,
                self.server_stats_file_watcher_2,
                self.server_config_file_watcher_2,
                USERS_DBM,
            )
        )
        armar_active_players.append(
            (
                bot,
                config.CHANNEL_IDS["Server Status"],
                3,
                self.server_stats_file_watcher_3,
                self.server_config_file_watcher_3,
                USERS_DBM,
            )
        )
        create_or_update_active_players_on_arma_reforger_server_status_message.start(
            armar_active_players
        )
        create_or_update_server_utilization_status_message.start(
            bot=bot, channel_id=config.CHANNEL_IDS["Stats"]
        )
        self.mods_active_messages_1.create_or_update_mod_messages.start()
        self.mods_active_messages_2.create_or_update_mod_messages.start()
        self.mods_active_messages_3.create_or_update_mod_messages.start()

    async def on_member_join(self, user):
        # Check if the member is already registered
        if USERS_DBM.read(user.id):
            USERS_DBM.update_status(user.id, "Active")
            ROLE_LOGS_DBM.create(
                user.id,
                user.id,
                "Unassigned",
                "User has rejoined the server",
            )
            log.info(f"{user.display_name} is already registered.")
        # register the user in the database
        else:
            USERS_DBM.create(user.id, user.name, user.display_name)
            ROLE_LOGS_DBM.create(
                user.id,
                user.id,
                "Unassigned",
                "User has joined the server",
            )
            log.info(f"Registered {user.display_name} in the database.")

        # Update the status message
        await create_or_update_teams_members_status_message(
            bot, config.CHANNEL_IDS["Stats"], USERS_DBM
        )

    async def on_member_update(self, before, after):
        member = after
        guild = member.guild
        user_bohemia_id = USERS_DBM.read_bohemia_id(member.id)

        # Check if the member has agreed to the rules
        if before.pending and not after.pending:
            old_team = USERS_DBM.read_team(member.id)
            role = guild.get_role(1350899518773919908)
            await member.add_roles(role)

            if old_team == "Unassigned":
                USERS_DBM.update_team(member.id, "Green Team")
            ROLE_LOGS_DBM.create(
                member.id,
                member.id,
                "Green Team",
                "User joined himself/herself as a Green Team member",
            )

        # Check for role changes
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            log.info(
                f"Member {member.display_name} roles updated. Added: {[role.name for role in added_roles]}, Removed: {[role.name for role in removed_roles]}"
            )

            for role in removed_roles:
                # Update team if the role is in TEAMS_ROLES
                if role.name in config.TEAMS_ROLES:
                    if (
                        USERS_DBM.read_team(member.id)
                        == config.TEAMS_ROLES[role.name][0]
                    ):
                        USERS_DBM.update_team(member.id, "Unassigned")

                    if not user_bohemia_id:
                        await send_embed(
                            channel=self.get_channel(config.CHANNEL_IDS["Logs"]),
                            description=f"User {member.display_name} does not have a Bohemia ID.",
                            color=discord.Color.red(),
                        )
                        continue

                    remove_player_from_playersgroups(
                        config.GET_ARMAR_PLAYERSGROUPS_FILE_PATH(1),
                        config.TEAMS_ROLES[role.name][1],
                        user_bohemia_id,
                    )
                    remove_player_from_playersgroups(
                        config.GET_ARMAR_PLAYERSGROUPS_FILE_PATH(2),
                        config.TEAMS_ROLES[role.name][1],
                        user_bohemia_id,
                    )
                    remove_player_from_playersgroups(
                        config.GET_ARMAR_PLAYERSGROUPS_FILE_PATH(3),
                        config.TEAMS_ROLES[role.name][1],
                        user_bohemia_id,
                    )

            for role in added_roles:
                # Update team if the role is in TEAMS_ROLES
                if role.name in config.TEAMS_ROLES:
                    if config.TEAMS_ROLES[role.name][0]:
                        USERS_DBM.update_team(
                            member.id, config.TEAMS_ROLES[role.name][0]
                        )

                    if not user_bohemia_id:
                        await send_embed(
                            channel=self.get_channel(config.CHANNEL_IDS["Logs"]),
                            description=f"User {member.display_name} does not have a Bohemia ID.",
                            color=discord.Color.red(),
                        )
                        continue

                    add_player_to_playersgroups(
                        config.GET_ARMAR_PLAYERSGROUPS_FILE_PATH(1),
                        config.TEAMS_ROLES[role.name][1],
                        user_bohemia_id,
                    )
                    add_player_to_playersgroups(
                        config.GET_ARMAR_PLAYERSGROUPS_FILE_PATH(2),
                        config.TEAMS_ROLES[role.name][1],
                        user_bohemia_id,
                    )
                    add_player_to_playersgroups(
                        config.GET_ARMAR_PLAYERSGROUPS_FILE_PATH(3),
                        config.TEAMS_ROLES[role.name][1],
                        user_bohemia_id,
                    )

    async def on_member_remove(self, user):
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

    async def on_message(self, message):
        if message.author.bot:
            return

        # Mod related message
        if message.channel.id == config.CHANNEL_IDS["Mods-Server-1"]:
            await self.mods_active_messages_1.handle_message(message)
        elif message.channel.id == config.CHANNEL_IDS["Mods-Server-2"]:
            await self.mods_active_messages_2.handle_message(message)
        elif message.channel.id == config.CHANNEL_IDS["Mods-Server-3"]:
            await self.mods_active_messages_3.handle_message(message)

    async def on_interaction(self, interaction):
        if interaction.data and "custom_id" in interaction.data:
            # Send interaction to log channel
            try:
                await send_embed(
                    channel=self.get_channel(config.CHANNEL_IDS["Logs"]),
                    description=f"User {interaction.user.display_name} used button {interaction.data["custom_id"]} in channel {interaction.channel_id}",
                    color=discord.Color.blue(),
                )
                log.info(
                    f"User {interaction.user.display_name} used button {interaction.data["custom_id"]} in channel {interaction.channel_id}"
                )
            except Exception as e:
                log.info(f"Unknown Exception: {e}")

            # Update Status Message
            if interaction.data["custom_id"] == "refresh_teams_members_status_message":
                # Acknowledge the button press
                await interaction.response.defer(ephemeral=True)

                # Call the update function
                await create_or_update_teams_members_status_message(
                    bot, config.CHANNEL_IDS["Stats"], USERS_DBM
                )
            # Update Status Message
            if (
                interaction.data["custom_id"]
                == "refresh_server_utilization_status_message"
            ):
                # Acknowledge the button press
                await interaction.response.defer(ephemeral=True)

                # Call the update function
                await create_or_update_server_utilization_status_message(
                    bot, config.CHANNEL_IDS["Stats"]
                )

            # Mod related interactions
            if interaction.channel_id == config.CHANNEL_IDS["Mods-Server-1"]:
                await interaction.response.defer(ephemeral=True)
                await self.mods_active_messages_1.handle_interaction(interaction)

            if interaction.channel_id == config.CHANNEL_IDS["Mods-Server-2"]:
                await interaction.response.defer(ephemeral=True)
                await self.mods_active_messages_2.handle_interaction(interaction)

            if interaction.channel_id == config.CHANNEL_IDS["Mods-Server-3"]:
                await interaction.response.defer(ephemeral=True)
                await self.mods_active_messages_3.handle_interaction(interaction)

    async def on_raw_reaction_add(self, payload):
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
            ROLE_LOGS_DBM.create(
                user_id,
                user_id,
                "Green Team",
                "User joined himself/herself as a Green Team member",
            )

            await create_or_update_teams_members_status_message(
                bot, config.CHANNEL_IDS["Stats"], USERS_DBM
            )

    async def shutdown(self):
        log.info("Shutdown initiated")

        # Stop file watchers
        # self.server_stats_file_watcher.stop()
        # self.server_config_file_watcher.stop()
        # self.server_config_file_watcher_test.stop()

        # Stop snapshotters
        self.loadout_snapshotter_1.stop()
        self.loadout_snapshotter_2.stop()
        self.loadout_snapshotter_3.stop()

        # Shutdown database connections
        # TODO: Implement database shutdown logic

        await bot.close()


intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
intents.reactions = True
intents.presences = True

# Create bot instance
bot = TalonBot(command_prefix="/", intents=intents)


# Main function to start the bot
async def main():
    try:
        await bot.start(config.BOT_TOKEN)
    except Exception as e:
        log.error(f"Bot crashed with exception: {e}")
        return 1
    return 0


if __name__ == "__main__":
    configure_logging(level=10)
    log = get_logger(__name__)

    sys.exit(asyncio.run(main()))
