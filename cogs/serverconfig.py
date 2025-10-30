import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config


class ServerConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash Command: /change_scenario
    @app_commands.command(name="change_scenario", description="Change server scenario")
    async def change_scenario(self, interaction: discord.Interaction, scenario_id: str):
        """
        Change the server scenario.

        Args:
            interaction (discord.Interaction): The interaction object.
            scenario (str): The new scenario to set.
        """
        # Check if the user is an admin
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=True
            )
            return

        # Update the server configuration file
        if not Path(config.SERVERCONFIG_PATH).is_file():
            await interaction.response.send_message(
                f"Server configuration file not found at {config.SERVERCONFIG_PATH}.",
                ephemeral=True,
            )
            return

        server_config = {}
        with open(config.SERVERCONFIG_PATH, "r") as file:
            server_config = json.load(file)

        if "game" not in server_config or "scenarioId" not in server_config["game"]:
            await interaction.response.send_message(
                f"Invalid server configuration file format at {config.SERVERCONFIG_PATH}.",
                ephemeral=True,
            )
            return

        server_config["game"]["scenarioId"] = scenario_id

        with open(config.SERVERCONFIG_PATH, "w") as file:
            json.dump(server_config, file, indent=4)

        await interaction.response.send_message(
            f"Scenario changed to {scenario_id}.", ephemeral=True
        )

    # Slash Command: /change_testserver_scenario
    @app_commands.command(
        name="change_testserver_scenario", description="Change test server scenario"
    )
    async def change_testserver_scenario(
        self, interaction: discord.Interaction, scenario_id: str
    ):
        """
        Change the test server scenario.

        Args:
            interaction (discord.Interaction): The interaction object.
            scenario (str): The new scenario to set.
        """
        # Check if the user is an admin
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=True
            )
            return

        # Update the test server configuration file
        if not Path(config.SERVERCONFIG_TEST_PATH).is_file():
            await interaction.response.send_message(
                f"Server configuration file not found at {config.SERVERCONFIG_TEST_PATH}.",
                ephemeral=True,
            )
            return

        server_config = {}
        with open(config.SERVERCONFIG_TEST_PATH, "r") as file:
            server_config = json.load(file)

        if "game" not in server_config or "scenarioId" not in server_config["game"]:
            await interaction.response.send_message(
                f"Invalid server configuration file format at {config.SERVERCONFIG_TEST_PATH}.",
                ephemeral=True,
            )
            return

        server_config["game"]["scenarioId"] = scenario_id

        with open(config.SERVERCONFIG_TEST_PATH, "w") as file:
            json.dump(server_config, file, indent=4)

        await interaction.response.send_message(
            f"Scenario changed to {scenario_id}.", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ServerConfigCog(bot))
