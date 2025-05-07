import discord
from discord import app_commands
from discord.ext import commands

import config

from utils.database_managers import USERS_DBM, ROLE_LOGS_DBM, MISCONDUCT_LOGS_DBM


class UserCog(commands.Cog):
    def __init__(self, bot, users_dbm, role_logs_dbm, misconduct_logs_dbm):
        self.bot = bot
        self.users_dbm = users_dbm
        self.role_logs_dbm = role_logs_dbm
        self.misconduct_logs_dbm = misconduct_logs_dbm

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


async def setup(bot):
    await bot.add_cog(UserCog(bot, USERS_DBM, ROLE_LOGS_DBM, MISCONDUCT_LOGS_DBM))
