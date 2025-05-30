import sys
import signal
import asyncio

import discord
from discord.ext import commands

import config
from utils.database_managers import (
    USERS_DBM,
    ROLE_LOGS_DBM,
)
from utils.file_watchers import (
    ServerAdminToolsStatsFileWatcher,
    ServerConfigFileWatcher,
)
from utils.active_messages import (
    create_or_update_server_utilization_status_message,
    create_or_update_teams_members_status_message,
    create_or_update_active_players_on_gameserver_status_message,
    ModsActiveMessages,
)


class TalonBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # File Watchers
        self.server_stats_file_watcher = ServerAdminToolsStatsFileWatcher(
            config.SERVERSTATS_PATH
        )
        self.server_config_file_watcher = ServerConfigFileWatcher(
            config.SERVERCONFIG_PATH
        )

        # Active Messages
        self.mods_active_messages = ModsActiveMessages(
            self,
            config.CHANNEL_IDS["Mods"],
            self.server_config_file_watcher,
        )

    async def setup_hook(self):
        # Load cogs here
        await self.load_extension("cogs.user")
        await self.load_extension("cogs.misc")
        await self.load_extension("cogs.serverconfig")
        await self.load_extension("cogs.mos")

        # Start file watcher
        self.server_stats_file_watcher.start()
        self.server_config_file_watcher.start()

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            for command in synced:
                print(f"✅ Synced slash command: {command.name}")
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")

        # Set up signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            bot.loop.add_signal_handler(
                sig, lambda: bot.loop.create_task(self.shutdown())
            )

    async def on_ready(self):
        print(f"✅ Logged in as {bot.user} (ID: {self.user.id})")

        # Set up active messages
        await create_or_update_teams_members_status_message(
            bot, config.CHANNEL_IDS["Stats"], USERS_DBM
        )

        # Set up self-looping active messages
        create_or_update_active_players_on_gameserver_status_message.start(
            bot=bot,
            channel_id=config.CHANNEL_IDS["Server Status"],
            server_stats=self.server_stats_file_watcher,
        )
        create_or_update_server_utilization_status_message.start(
            bot=bot, channel_id=config.CHANNEL_IDS["Stats"]
        )
        self.mods_active_messages.create_or_update_mod_messages.start()

    async def on_member_join(self, user):
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

    async def on_member_update(self, before, after):
        # Check if the member has agreed to the rules
        if before.pending and not after.pending:
            member = after
            guild = member.guild

            old_team = USERS_DBM.read_team(member.id)
            role = guild.get_role(1350899518773919908)
            await member.add_roles(role)

            if old_team == "Unassigned":
                USERS_DBM.update_team(member.id, "Green Team")
                USERS_DBM.reset_joined(member.id)
            ROLE_LOGS_DBM.create(
                member.id,
                member.id,
                "Green Team",
                "User joined himself/herself as a Green Team member",
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
        if message.channel.id == config.CHANNEL_IDS["Mods"]:
            await self.mods_active_messages.handle_message(message)

    async def on_interaction(self, interaction):
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
            if interaction.channel_id == config.CHANNEL_IDS["Mods"]:
                # Acknowledge the button press
                await interaction.response.defer(ephemeral=True)

                # Call the update function
                await self.mods_active_messages.handle_interaction(interaction)

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

    async def shutdown(self):
        print("Shutdown initiated")

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
        print(f"Bot crashed with exception: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
