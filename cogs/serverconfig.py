import json
from pathlib import Path

import config
import discord
from discord import app_commands
from discord.ext import commands


class ServerConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash Command: /change_reforger_server_scenario
    @app_commands.command(
        name="change_reforger_server_scenario",
        description="Change arma reforger server scenario",
    )
    @app_commands.describe(
        server_number="The server number to start (1, 2, ...).",
        scenario_id="The new scenario ID (example: {ECC61978EDCC2B5A}Missions/23_Campaign.conf).",
    )
    async def change_reforger_server_scenario(
        self, interaction: discord.Interaction, server_number: int, scenario_id: str
    ):
        # Check if the user is an admin
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=True
            )
            return

        # Update the server configuration file
        if not Path(config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number)).is_file():
            await interaction.response.send_message(
                f"Server configuration file not found at {config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number)}.",
                ephemeral=True,
            )
            return

        server_config = {}
        with open(config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number), "r") as file:
            server_config = json.load(file)

        if "game" not in server_config or "scenarioId" not in server_config["game"]:
            await interaction.response.send_message(
                f"Invalid server configuration file format at {config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number)}.",
                ephemeral=True,
            )
            return

        server_config["game"]["scenarioId"] = scenario_id

        with open(config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number), "w") as file:
            json.dump(server_config, file, indent=4)

        await interaction.response.send_message(
            f"Server {server_number} Scenario changed to {scenario_id}.", ephemeral=True
        )

    # Slash Command: /rename_reforger_server
    @app_commands.command(
        name="rename_reforger_server",
        description="Rename arma reforger server",
    )
    @app_commands.describe(
        server_number="The server number to start (1, 2, ...).",
        name="The new server name.",
    )
    async def rename_reforger_server(
        self, interaction: discord.Interaction, server_number: int, name: str
    ):
        # Check if the user is an admin
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=True
            )
            return

        # Update the server configuration file
        if not Path(config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number)).is_file():
            await interaction.response.send_message(
                f"Server configuration file not found at {config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number)}.",
                ephemeral=True,
            )
            return

        server_config = {}
        with open(config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number), "r") as file:
            server_config = json.load(file)

        if "game" not in server_config or "name" not in server_config["game"]:
            await interaction.response.send_message(
                f"Invalid server configuration file format at {config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number)}.",
                ephemeral=True,
            )
            return

        server_config["game"]["name"] = name

        with open(config.GET_ARMAR_SERVERCONFIG_FILE_PATH(server_number), "w") as file:
            json.dump(server_config, file, indent=4)

        await interaction.response.send_message(
            f"Server {server_number} Name changed to {name}.", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ServerConfigCog(bot))
