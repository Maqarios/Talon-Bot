import discord
from discord import app_commands
from discord.ext import commands

import config

from utils.database_managers import USERS_DBM, ROLE_LOGS_DBM, MISCONDUCT_LOGS_DBM
from utils.cache import ACTIVE_PLAYERS_BOHEMIA_ID_CACHE
from utils.active_messages import create_or_update_teams_members_status_message
from utils.utils import (
    add_player_to_playersgroups,
    remove_player_from_playersgroups,
)


class UserCog(commands.Cog):
    def __init__(
        self, bot, users_dbm, role_logs_dbm, misconduct_logs_dbm, bohemia_id_cache
    ):
        self.bot = bot
        self.users_dbm = users_dbm
        self.role_logs_dbm = role_logs_dbm
        self.misconduct_logs_dbm = misconduct_logs_dbm
        self.bohemia_id_cache = bohemia_id_cache

    # Slash Command: /register
    @app_commands.command(
        name="register", description="Register yourself in the database."
    )
    async def register(self, interaction: discord.Interaction):
        user = interaction.user

        self.users_dbm.create(user.id, user.name, user.display_name)
        self.role_logs_dbm.create(
            user.id, user.id, "Unassigned", "User registered himself/herself"
        )
        await interaction.response.send_message(
            f"Registered {user.name} in the database.", ephemeral=True
        )

    # Slash Command: /register_user
    @app_commands.command(
        name="register_user", description="Register a user in the database"
    )
    @app_commands.describe(user="The user to register")
    async def register_user(self, interaction: discord.Interaction, user: discord.User):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        self.users_dbm.create(user.id, user.name, user.display_name)
        self.role_logs_dbm.create(
            interaction.user.id, user.id, "Unassigned", "User was registered by admin"
        )
        await interaction.response.send_message(
            f"Registered {user.name} in the database.", ephemeral=True
        )

    # Slash Command: /delete_user
    @app_commands.command(
        name="delete_user", description="Delete a user from the database"
    )
    @app_commands.describe(user="The user to delete")
    async def delete_user(self, interaction: discord.Interaction, user: discord.User):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        self.users_dbm.delete(user.id)
        self.role_logs_dbm.mark_as_deleted_by_instigator_discord_id(user.id)
        self.role_logs_dbm.mark_as_deleted_by_target_discord_id(user.id)
        self.misconduct_logs_dbm.mark_as_deleted_by_instigator_discord_id(user.id)
        self.misconduct_logs_dbm.mark_as_deleted_by_target_discord_id(user.id)
        self.misconduct_logs_dbm.mark_as_deleted_by_victim_discord_id(user.id)
        await interaction.response.send_message(
            f"Deleted {user.name} from the database.", ephemeral=True
        )

    # Slash Command: /show_user_team_logs
    @app_commands.command(
        name="show_user_team_logs", description="Show a user's team logs"
    )
    @app_commands.describe(user="The user to show logs for")
    async def show_user_team_logs(
        self, interaction: discord.Interaction, user: discord.User
    ):
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

    # Slash Command: /link_user_bohemia_id
    @app_commands.command(
        name="link_user_bohemia_id",
        description="Link a player bohemia id to the users database",
    )
    @app_commands.describe(
        user="The user to link bohemia id for", in_game_name="The bohemia id to link"
    )
    async def link_user_bohemia_id(
        self, interaction: discord.Interaction, user: discord.User, in_game_name: str
    ):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        USERS_DBM.update_bohemia_id(user.id, in_game_name)
        self.bohemia_id_cache.add_known_player(user.id, in_game_name)
        self.bohemia_id_cache.remove_unknown_player(in_game_name)
        await interaction.response.send_message(
            f"Added {in_game_name} to {user.name}'s bohemia id.", ephemeral=True
        )

    @link_user_bohemia_id.autocomplete("in_game_name")
    async def in_game_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[discord.app_commands.Choice[str]]:
        unknown_players = self.bohemia_id_cache.get_unknown_players()

        return [
            discord.app_commands.Choice(name=player_name, value=str(player_bohemia_id))
            for player_bohemia_id, player_name in unknown_players.items()
            if current.lower() in player_name.lower()
        ][:25]


class MisconductCog(commands.Cog):
    def __init__(self, bot, users_dbm, misconduct_logs_dbm):
        self.bot = bot
        self.users_dbm = users_dbm
        self.misconduct_logs_dbm = misconduct_logs_dbm

    # Slash Command: /add_misconduct
    @app_commands.command(
        name="add_misconduct", description="Add a misconduct to a user in the database"
    )
    @app_commands.describe(
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
        severity=[
            discord.app_commands.Choice(name="Green", value=0),
            discord.app_commands.Choice(name="Yellow", value=1),
            discord.app_commands.Choice(name="Red", value=2),
        ],
    )
    async def add_misconduct(
        self,
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
        self.misconduct_logs_dbm.create(
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

    @add_misconduct.autocomplete("type")
    async def misconduct_type_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        category = interaction.namespace.category

        # Return all types as Choice objects
        if not category or category not in config.MISCONDUCT_CATEGORIES:
            all_types = [
                item
                for sublist in config.MISCONDUCT_CATEGORIES.values()
                for item in sublist
            ]
            return [
                discord.app_commands.Choice(name=item, value=item)
                for item in all_types
                if current.lower() in item.lower()
            ][:25]

        # Return types for selected category
        return [
            discord.app_commands.Choice(name=item, value=item)
            for item in config.MISCONDUCT_CATEGORIES[category]
            if current.lower() in item.lower()
        ][:25]

    # Slash Command: /show_misconducts
    @app_commands.command(
        name="show_misconducts", description="Show a user's misconduct logs"
    )
    @app_commands.describe(user="The user to show misconducts for")
    async def show_misconducts(
        self, interaction: discord.Interaction, user: discord.User
    ):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        message = ""
        for entry in self.misconduct_logs_dbm.read_by_target_discord_id(user.id):
            user_a_discord_displayname = self.users_dbm.read_discord_displayname(
                entry[1]
            )
            user_b_discord_displayname = self.users_dbm.read_discord_displayname(
                entry[2]
            )
            user_c_discord_displayname = (
                self.users_dbm.read_discord_displayname(entry[3])
                if entry[3] is not None
                else "N/A"
            )
            message += f"Initiator: {user_a_discord_displayname}\nAccused: {user_b_discord_displayname}\nVictim: {user_c_discord_displayname}\nCategory: {entry[4]}\nType: {entry[5]}\nDetails: {entry[6]}\nSeverity: {entry[7]}\nTimestamp: {entry[8]}\n\n"

        await interaction.response.send_message(message)


async def setup(bot):
    await bot.add_cog(
        UserCog(
            bot,
            USERS_DBM,
            ROLE_LOGS_DBM,
            MISCONDUCT_LOGS_DBM,
            ACTIVE_PLAYERS_BOHEMIA_ID_CACHE,
        )
    )
    await bot.add_cog(MisconductCog(bot, USERS_DBM, MISCONDUCT_LOGS_DBM))
