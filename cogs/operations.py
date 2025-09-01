import datetime

import discord
from discord import app_commands, InteractionType
from discord.ext import commands
from discord.ui import Button, View

import config

from utils.utils import get_channel, send_embed
from utils.loggers import get_logger

log = get_logger(__name__)


class OperationsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Make an interactive message for joining an operation
    async def make_join_or_leave_operation_message(self, thread):
        # Create Discord embed for better formatting
        embed = discord.Embed(
            title="New Operation",
            description="Click the button below to join the operation!",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(),
        )

        # Create the view with buttons
        view = View(timeout=None)

        # Create buttons
        join_button = Button(
            style=discord.ButtonStyle.green,
            label="Join",
            custom_id=f"join_operation:{thread.id}",
        )
        view.add_item(join_button)

        leave_button = Button(
            style=discord.ButtonStyle.red,
            label="Abandon",
            custom_id=f"leave_operation:{thread.id}",
        )
        view.add_item(leave_button)

        return embed, view

    # Slash Command: /create_operation
    @app_commands.command(
        name="create_operation", description="Create a new operation."
    )
    @app_commands.describe(name="The name of the operation")
    async def create_operation(self, interaction: discord.Interaction, name: str):
        if interaction.user.id not in config.ADMIN_IDS:
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
            return

        try:
            channel = get_channel(self.bot, config.CHANNEL_IDS["Testing"])
            thread = await channel.create_thread(
                name=name,
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread,
                invitable=False,
            )
            log.debug(thread)
            log.debug(thread.id)

            embed, view = await self.make_join_or_leave_operation_message(thread)
            await channel.send(embed=embed, view=view)

            await interaction.response.send_message(
                "Operation created successfully!", ephemeral=True
            )
            await send_embed(
                channel=get_channel(self.bot, config.CHANNEL_IDS["Logs"]),
                title="Operation Created",
                description=f"{interaction.user} created an operation.",
                color=discord.Color.green(),
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Bot doesn't have enough permissions.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Unexpected error: {e}", ephemeral=True
            )

        await interaction.response.send_message(
            f"Thread created: {thread.name}", ephemeral=True
        )

    # Static function for handling button interactions
    @staticmethod
    async def handle_interaction(bot, interaction: discord.Interaction):
        if interaction.type == InteractionType.component:
            if interaction.data["component_type"] == 2:
                log.debug(
                    f"Button interaction received: {interaction.data['custom_id']}"
                )
                custom_id = interaction.data["custom_id"].split(":")
                message_type = custom_id[0]

                if message_type == "join_operation":
                    thread_id = custom_id[1]
                    thread = await bot.fetch_channel(thread_id)
                    await thread.add_user(interaction.user)
                    await interaction.response.send_message(
                        f"You have joined the operation in thread {thread_id}.",
                        ephemeral=True,
                    )
                elif message_type == "leave_operation":
                    thread_id = custom_id[1]
                    thread = await bot.fetch_channel(thread_id)
                    await thread.remove_user(interaction.user)
                    await interaction.response.send_message(
                        f"You have left the operation in thread {thread_id}.",
                        ephemeral=True,
                    )


async def setup(bot):
    await bot.add_cog(OperationsCog(bot))
