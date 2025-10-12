import json
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config

from utils.database_managers import USERS_DBM

from utils.loggers import get_logger

log = get_logger(__name__)

class MosCog(commands.Cog):
    def __init__(self, bot, users_dbm, profile_dir_path):
        self.bot = bot
        self.users_dbm = users_dbm
        self.profile_dir_path = profile_dir_path

        self.RIFLEMAN = 0
        self.LMG = 1
        self.CMT = 2
        self.LS = 3
        self.JTAC = 4
        self.DAB = 5
        self.GRENADIER = 6
        self.MARKSMAN = 7

    def _get_bacon_loadout_path(self, bohemia_id, is_file=True):
        if is_file:
            return f"{self.profile_dir_path}/BaconLoadoutEditor_Loadouts/1.4/US/{bohemia_id[:2]}/{bohemia_id}"
        
        return f"{self.profile_dir_path}/BaconLoadoutEditor_Loadouts/1.4/US/{bohemia_id[:2]}"

    def _get_persistent_loadout_path(self, bohemia_id, is_file=True):
        if is_file:
            return f"{self.profile_dir_path}/GMPersistentLoadouts/v2/US/{bohemia_id[:2]}/{bohemia_id}"
        
        return f"{self.profile_dir_path}/GMPersistentLoadouts/v2/US/{bohemia_id[:2]}"

    def _get_bacon_admin_loadout_path(self):
        return f"{self.profile_dir_path}/BaconLoadoutEditor_Loadouts/1.4/admin_loadouts"

    # Slash Command: /delete_user_loadout
    @app_commands.command(
        name="delete_user_loadout", description="Delete the given user's loadout."
    )
    @app_commands.describe(user="The user to delete the loadout for")
    async def delete_user_loadout(
        self, interaction: discord.Interaction, user: discord.User
    ):
        is_MP = False
        for role in interaction.user.roles:
            if role.id == config.MP_ROLE_ID:
                is_MP = True
                break
        if not is_MP:
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

        # Get directory paths for the user's sections
        bacon_dir = Path(self._get_bacon_loadout_path(target_user_bohemia_id, is_file=False))
        persistent_dir = Path(self._get_persistent_loadout_path(target_user_bohemia_id, is_file=False))

        deleted_files = []
        
        # Delete all files starting with the user's bohemia_id in bacon loadout directory
        if bacon_dir.exists():
            for file_path in bacon_dir.glob(f"{target_user_bohemia_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_files.append(str(file_path))
        
        # Delete all files starting with the user's bohemia_id in persistent loadout directory
        if persistent_dir.exists():
            for file_path in persistent_dir.glob(f"{target_user_bohemia_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_files.append(str(file_path))

        if deleted_files:
            await interaction.response.send_message(
                f"Deleted {len(deleted_files)} loadout files for user {user.display_name}.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"No loadout files found for user {user.display_name}.",
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
        is_MP = False
        for role in interaction.user.roles:
            if role.id == config.MP_ROLE_ID:
                is_MP = True
                break
        if not is_MP:
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
        is_MP = False
        for role in interaction.user.roles:
            if role.id == config.MP_ROLE_ID:
                is_MP = True
                break
        if not is_MP:
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

    # Slash Command: /give_user_kit
    @app_commands.command(
        name="give_user_kit", description="Give the specified user a kit."
    )
    @app_commands.describe(
        user="The user to give the kit to", kit="Kit name", slot="Slot index"
    )
    @app_commands.choices(
        kit=[
            app_commands.Choice(name="RIFLEMAN", value="rifleman"),
            app_commands.Choice(name="LMG", value="lmg"),
            app_commands.Choice(name="CMT", value="cmt"),
            app_commands.Choice(name="LS", value="ls"),
            app_commands.Choice(name="JTAC", value="jtac"),
            app_commands.Choice(name="DAB", value="dab"),
            app_commands.Choice(name="GRENADIER", value="grenadier"),
            app_commands.Choice(name="MARKSMAN", value="marksman"),
        ]
    )
    async def give_user_kit(
        self, interaction: discord.Interaction, user: discord.User, kit: str, slot: int
    ):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        match kit:
            case "rifleman":
                kit_index = self.RIFLEMAN
            case "lmg":
                kit_index = self.LMG
            case "cmt":
                kit_index = self.CMT
            case "ls":
                kit_index = self.LS
            case "jtac":
                kit_index = self.JTAC
            case "dab":
                kit_index = self.DAB
            case "grenadier":
                kit_index = self.GRENADIER
            case "marksman":
                kit_index = self.MARKSMAN
            case _:
                await interaction.response.send_message(
                    f"Invalid kit specified: {kit}.", ephemeral=True
                )
                return
        slot -= 1  # Convert to 0-indexed

        target_user_bohemia_id = self.users_dbm.read_bohemia_id(user.id)
        if target_user_bohemia_id is None:
            await interaction.response.send_message(
                f"User {user.display_name} does not have a Bohemia ID registered.",
                ephemeral=True,
            )
            return

        admin_bacon_loadout_path = self._get_bacon_admin_loadout_path()
        target_user_bacon_loadout_path = self._get_bacon_loadout_path(
            target_user_bohemia_id
        )

        try:
            admin_loadouts = None
            with open(admin_bacon_loadout_path, "r") as f:
                admin_loadouts = json.load(f)

            target_loadouts = None
            with open(target_user_bacon_loadout_path, "r") as f:
                target_loadouts = json.load(f)

            target_loadouts["playerLoadouts"]["US"][str(slot)] = admin_loadouts[
                "playerLoadouts"
            ]["admin"][str(kit_index)]
            target_loadouts["playerLoadouts"]["US"][str(slot)]["slotId"] = slot

            with open(target_user_bacon_loadout_path, "w") as f:
                json.dump(target_loadouts, f, indent=4)

        except Exception as e:
            await interaction.response.send_message(
                f"Error processing loadouts: {e}", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Gave {user.display_name} the {kit.upper()} kit in slot {slot + 1}.",
            ephemeral=True,
        )

    # Slash Command: /load_backup_loadout
    @app_commands.command(
        name="load_backup_loadout", description="Load a backup loadout."
    )
    @app_commands.describe(save="Which save to restore")
    async def load_backup_loadout(
        self, interaction: discord.Interaction, save: str
    ):
        user_bohemia_id = self.users_dbm.read_bohemia_id(interaction.user.id)
        if user_bohemia_id is None:
            await interaction.response.send_message(
                f"You do not have a Bohemia ID registered. Contact an admin to register you.",
                ephemeral=True,
            )
            return

        current_loadout_path = Path(self._get_bacon_loadout_path(user_bohemia_id))
        chosen_loadout_path = Path(f"{self._get_bacon_loadout_path(user_bohemia_id)}_{save}")
        
        try:
            current_loadout_path.unlink()
            chosen_loadout_path.rename(current_loadout_path)
        except Exception as e:
            await interaction.response.send_message(
                f"Error loading backup kit: {e}", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Loaded backup kit {save}.",
            ephemeral=True,
        )

    @load_backup_loadout.autocomplete("save")
    async def save_autocomplete(self, interaction: discord.Interaction, current: str):
        user_bohemia_id = self.users_dbm.read_bohemia_id(interaction.user.id)
        if user_bohemia_id is None:
            return []
        
        options = []
        
        # Get directory paths for the user's sections
        bacon_dir = Path(self._get_bacon_loadout_path(user_bohemia_id, is_file=False))
        
        # Delete all files starting with the user's bohemia_id in bacon loadout directory
        if bacon_dir.exists():
            for file_path in sorted(bacon_dir.glob(f"{user_bohemia_id}_*"), reverse=True):
                if file_path.is_file():
                    options.append(file_path.stem.replace(f"{user_bohemia_id}_", ""))
        
        # Since most recent kit is the current kit, we gonna skip it
        if len(options) > 0:
            options = options[1:]
        
        choices = []
        for opt in options:
            if current.lower() in opt.lower():
                name = datetime.strptime(opt, config.SNAPSHOT_FORMAT)
                name = f"Date: {name.strftime('%d.%m.%Y')}, Time: {name.strftime('%H:%M:%S')}"
                
                choices.append(app_commands.Choice(name=name, value=opt))
        
        return choices[:25]  # Discord allows max 25 choices

async def setup(bot):
    await bot.add_cog(MosCog(bot, USERS_DBM, config.PROFILE_DIR_PATH))
