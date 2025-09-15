from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config

from utils.database_managers import USERS_DBM


class MosCog(commands.Cog):
    def __init__(self, bot, users_dbm, profile_dir_path):
        self.bot = bot
        self.users_dbm = users_dbm
        self.profile_dir_path = profile_dir_path

    def _get_bacon_loadout_path(self, bohemia_id):
        return f"{self.profile_dir_path}/BaconLoadoutEditor_Loadouts/1.4/US/{bohemia_id[:2]}/{bohemia_id}"

    def _get_persistent_loadout_path(self, bohemia_id):
        return f"{self.profile_dir_path}/GMPersistentLoadouts/v2/US/{bohemia_id[:2]}/{bohemia_id}"

    # Slash Command: /delete_user_loadout
    @app_commands.command(
        name="delete_user_loadout", description="Delete the given user's loadout."
    )
    @app_commands.describe(user="The user to delete the loadout for")
    async def delete_user_loadout(
        self, interaction: discord.Interaction, user: discord.User
    ):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        target_user_bohemia_id = self.users_dbm.read_bohemia_id(user.id)
        if target_user_bohemia_id is None:
            await interaction.response.send_message(
                f"User {user.display_name} does not have a Bohemia ID registered.",
                ephemeral=True,
            )
            return

        target_user_bacon_loadout_path = self._get_bacon_loadout_path(
            target_user_bohemia_id
        )
        target_user_persistent_loadout_path = self._get_persistent_loadout_path(
            target_user_bohemia_id
        )

        if Path(target_user_bacon_loadout_path).is_file():
            Path(target_user_bacon_loadout_path).unlink()

        if Path(target_user_persistent_loadout_path).is_file():
            Path(target_user_persistent_loadout_path).unlink()

        await interaction.response.send_message(
            f"Loadouts deleted for user {user.display_name}.",
            ephemeral=True,
        )

    # Slash Command: /start_mos_check
    @app_commands.command(
        name="start_mos_check", description="Get the given user's loadout."
    )
    @app_commands.describe(user="The user to get the loadout for")
    async def start_mos_check(
        self, interaction: discord.Interaction, user: discord.User
    ):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        instigator_user_bohemia_id = self.users_dbm.read_bohemia_id(interaction.user.id)
        if instigator_user_bohemia_id is None:
            await interaction.response.send_message(
                f"User {interaction.user.display_name} does not have a Bohemia ID registered.",
                ephemeral=True,
            )
            return

        target_user_bohemia_id = self.users_dbm.read_bohemia_id(user.id)
        if target_user_bohemia_id is None:
            await interaction.response.send_message(
                f"User {user.display_name} does not have a Bohemia ID registered.",
                ephemeral=True,
            )
            return

        instigator_user_bacon_loadout_path = self._get_bacon_loadout_path(
            instigator_user_bohemia_id
        )
        instigator_user_persistent_loadout_path = self._get_persistent_loadout_path(
            instigator_user_bohemia_id
        )

        target_user_bacon_loadout_path = self._get_bacon_loadout_path(
            target_user_bohemia_id
        )
        target_user_persistent_loadout_path = self._get_persistent_loadout_path(
            target_user_bohemia_id
        )

        if not Path(instigator_user_bacon_loadout_path + ".backup").is_file():
            Path(instigator_user_bacon_loadout_path).rename(
                instigator_user_bacon_loadout_path + ".backup"
            )
        if not Path(instigator_user_persistent_loadout_path + ".backup").is_file():
            Path(instigator_user_persistent_loadout_path).rename(
                instigator_user_persistent_loadout_path + ".backup"
            )

        if Path(target_user_bacon_loadout_path).is_file():
            loadout = Path(target_user_bacon_loadout_path).read_text()
            Path(instigator_user_bacon_loadout_path).write_text(loadout)

        if Path(target_user_persistent_loadout_path).is_file():
            loadout = Path(target_user_persistent_loadout_path).read_text()
            Path(instigator_user_persistent_loadout_path).write_text(loadout)

        await interaction.response.send_message(
            f"Loadouts copied from {user.display_name} to {interaction.user.display_name}.",
            ephemeral=True,
        )

    # Slash Command: /stop_mos_check
    @app_commands.command(name="stop_mos_check", description="Stop the loadout check.")
    async def stop_mos_check(self, interaction: discord.Interaction):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        instigator_user_bohemia_id = self.users_dbm.read_bohemia_id(interaction.user.id)
        if instigator_user_bohemia_id is None:
            await interaction.response.send_message(
                f"User {interaction.user.display_name} does not have a Bohemia ID registered.",
                ephemeral=True,
            )
            return

        instigator_user_bacon_loadout_path = self._get_bacon_loadout_path(
            instigator_user_bohemia_id
        )
        instigator_user_persistent_loadout_path = self._get_persistent_loadout_path(
            instigator_user_bohemia_id
        )

        if Path(instigator_user_bacon_loadout_path + ".backup").is_file():
            if Path(instigator_user_bacon_loadout_path).is_file():
                Path(instigator_user_bacon_loadout_path).unlink()
            Path(instigator_user_bacon_loadout_path + ".backup").rename(
                instigator_user_bacon_loadout_path
            )
        if Path(instigator_user_persistent_loadout_path + ".backup").is_file():
            if Path(instigator_user_persistent_loadout_path).is_file():
                Path(instigator_user_persistent_loadout_path).unlink()
            Path(instigator_user_persistent_loadout_path + ".backup").rename(
                instigator_user_persistent_loadout_path
            )

        await interaction.response.send_message(
            "Loadouts restored to their original state.", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(MosCog(bot, USERS_DBM, config.PROFILE_DIR_PATH))
