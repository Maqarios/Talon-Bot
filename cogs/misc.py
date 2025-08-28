import subprocess

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.utils import restart_gameserver as restart_gameserver_util
from utils.utils import update_gameserver as update_gameserver_util


class MiscCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash Command: /ping
    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds
        await interaction.response.send_message(
            f"Pong! Latency: {latency}ms", ephemeral=True
        )

    # Slash Command: /privacy
    @app_commands.command(name="privacy", description="Privacy policy.")
    async def privacy(self, interaction: discord.Interaction):
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

    # Slash Command: /restart_gameserver
    @app_commands.command(
        name="restart_gameserver", description="Restart the game server."
    )
    async def restart_gameserver(self, interaction: discord.Interaction):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        try:
            restart_gameserver_util()
            await interaction.response.send_message(
                "Game server is restarting...", ephemeral=True
            )
        except subprocess.CalledProcessError as e:
            await interaction.response.send_message(
                f"Failed to restart the game server: {e}", ephemeral=True
            )

    # Slash Command: /update_gameserver
    @app_commands.command(
        name="update_gameserver", description="Update the game server."
    )
    async def update_gameserver(self, interaction: discord.Interaction):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        # Acknowledge the command
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            update_gameserver_util()
            await interaction.edit_original_response(content="Game server is updated.")
        except subprocess.CalledProcessError as e:
            await interaction.edit_original_response(
                content=f"Failed to update the game server: {e}"
            )


async def setup(bot):
    await bot.add_cog(MiscCog(bot))
