import os
import subprocess
import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path

import psutil
import discord

from utils.loggers import get_logger

log = get_logger(__name__)


# Check if a specific port is listening (i.e. gameserver)
def is_port_listening(port: int = 2001) -> bool:
    """
    Check if a given TCP/UDP port is currently listening on the local machine.

    Args:
        port (int, optional): The port number to check. Must be between 1 and 65535. Defaults to 2001.

    Returns:
        bool: True if the port is listening, False otherwise.

    Raises:
        ValueError: If the port number is not within the valid range.

    Logs:
        Errors and exceptions encountered during execution are logged using the `log` object.
    """
    try:
        if not (1 <= port <= 65535):
            raise ValueError("Port number must be between 1 and 65535")

        result = subprocess.run(
            ["ss", "-tuln", f"sport = :{port}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        if result.returncode != 0:
            log.error(
                f"ss command failed with return code {result.returncode}: {result.stderr.strip()}"
            )
            return False

        return any(f":{port}" in line for line in result.stdout.splitlines())

    except ValueError as e:
        log.error(f"Invalid port {port}: {e}")
        return False
    except subprocess.TimeoutExpired:
        log.error("ss command timed out")
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"ss command failed: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error checking port {port}: {e}")
        return False


# CPU, Memory and Disk usage
def get_server_utilization() -> tuple[float, float, float]:
    """
    Retrieves the current server utilization statistics for CPU, memory, and disk usage.

    Attempts to use the `psutil` library for accurate readings. If `psutil` fails,
    falls back to using shell commands via `subprocess` to obtain the metrics.

    Returns:
        tuple: A tuple containing three floats:
            - cpu (float): CPU usage percentage.
            - memory (float): Memory usage percentage.
            - disk (float): Disk usage percentage.

    Logs errors if unable to retrieve any of the metrics, and returns 0.0 for failed readings.
    """
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        return cpu, memory, disk

    except Exception as e:
        log.error(f"Error getting server utilization via psutil: {e}")

        # Fallback to subprocess method if psutil fails
        try:
            cpu = float(
                subprocess.check_output(
                    "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", shell=True
                )
                .decode()
                .strip()
            )
        except Exception as e:
            log.error(f"Error getting CPU usage via subprocess: {e}")
            cpu = 0.0

        try:
            memory = float(
                subprocess.check_output(
                    "free -m | grep Mem | awk '{print $3/$2 * 100.0}'", shell=True
                )
                .decode()
                .strip()
            )
        except Exception as e:
            log.error(f"Error getting memory usage via subprocess: {e}")
            memory = 0.0

        try:
            disk = float(
                subprocess.check_output("df -h / | awk 'NR==2 {print $5}'", shell=True)
                .decode()
                .strip()[:-1]
            )
        except Exception as e:
            log.error(f"Error getting disk usage via subprocess: {e}")
            disk = 0.0

        return cpu, memory, disk


# Restart the gameserver
def restart_gameserver() -> bool:
    """
    Attempts to restart the Arma Reforger game server using systemctl.

    Executes the command 'sudo systemctl restart arma-reforger-server' with a timeout of 5 seconds.
    Logs errors if the restart fails, times out, or encounters unexpected exceptions.

    Returns:
        bool: True if the server was restarted successfully, False otherwise.
    """
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "arma-reforger-server"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        if result.returncode != 0:
            log.error(
                f"Failed to restart gameserver, bash script returned {result.returncode}: {result.stderr.strip()}"
            )
            return False

        log.info("Gameserver restarted successfully.")
        return True

    except subprocess.TimeoutExpired:
        log.error("Gameserver restart command timed out")
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"Gameserver restart command failed: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error restarting gameserver: {e}")
        return False


# Update the gameserver
def update_gameserver() -> bool:
    """
    Updates the gameserver by executing a bash script.

    Runs the install_or_update.sh script located in the user's Desktop/ArmaR directory.
    Logs errors if the script fails, times out, or encounters unexpected exceptions.

    Returns:
        bool: True if the update was successful, False otherwise.
    """

    try:
        result = subprocess.run(
            ["bash", os.path.expanduser("~/Desktop/ArmaR/install_or_update.sh")],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )

        if result.returncode != 0:
            log.error(
                f"Failed to update gameserver, bash script returned {result.returncode}: {result.stderr.strip()}"
            )
            return False

        log.info("Gameserver updated successfully.")
        return True

    except subprocess.TimeoutExpired:
        log.error("Gameserver update command timed out")
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"Gameserver update command failed: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error updating gameserver: {e}")
        return False


# Start the testserver
def start_testserver() -> bool:
    """
    Attempts to start the Arma Reforger test server using systemctl.

    Runs the command 'sudo systemctl start arma-reforger-test-server' with a timeout of 5 seconds.
    Logs errors if the command fails, times out, or encounters an unexpected exception.

    Returns:
        bool: True if the server started successfully, False otherwise.
    """
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "start", "arma-reforger-test-server"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        if result.returncode != 0:
            log.error(
                f"Failed to start testserver, bash script returned {result.returncode}: {result.stderr.strip()}"
            )
            return False

        log.info("Testserver started successfully.")
        return True

    except subprocess.TimeoutExpired:
        log.error("Testserver start command timed out")
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"Testserver start command failed: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error starting testserver: {e}")
        return False


# Restart the testserver
def restart_testserver() -> bool:
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "arma-reforger-test-server"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        if result.returncode != 0:
            log.error(
                f"Failed to restart testserver, bash script returned {result.returncode}: {result.stderr.strip()}"
            )
            return False

        log.info("Testserver restarted successfully.")
        return True

    except subprocess.TimeoutExpired:
        log.error("Testserver restart command timed out")
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"Testserver restart command failed: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error restarting testserver: {e}")
        return False


# Stop the testserver
def stop_testserver() -> bool:
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "stop", "arma-reforger-test-server"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )

        if result.returncode != 0:
            log.error(
                f"Failed to stop testserver, bash script returned {result.returncode}: {result.stderr.strip()}"
            )
            return False

        log.info("Testserver stopped successfully.")
        return True

    except subprocess.TimeoutExpired:
        log.error("Testserver stop command timed out")
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"Testserver stop command failed: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error stopping testserver: {e}")
        return False


def get_active_messages_id(activemessagesids_path, entry):
    # Check if the file exists
    if not Path(activemessagesids_path).is_file():
        print(f"File {activemessagesids_path} does not exist. Creating a new file.")

        # Create the file if it doesn't exist
        with open(activemessagesids_path, "w") as file:
            json.dump({}, file, indent=4)

        raise FileNotFoundError(
            f"File {activemessagesids_path} does not exist. A new file has been created."
        )

    # Read the JSON file
    data = {}
    with open(activemessagesids_path, "r") as file:
        data = json.load(file)

    # Check if entry not in file
    if entry not in data:
        print(f"Entry '{entry}' not found in {activemessagesids_path}.")
        raise KeyError(f"Entry '{entry}' not found in {activemessagesids_path}.")

    return data[entry]


def set_active_messages_id(activemessagesids_path, entry, messages_id=None):
    # Check if the file exists
    if not Path(activemessagesids_path).is_file():
        print(f"File {activemessagesids_path} does not exist. Creating a new file.")

        # Create the file if it doesn't exist
        with open(activemessagesids_path, "w") as file:
            json.dump({}, file, indent=4)

        return None

    # Read the JSON file
    data = {}
    with open(activemessagesids_path, "r") as file:
        data = json.load(file)

    # Update the entry with new messages_ids
    if messages_id is not None:
        data[entry] = messages_id
    elif entry in data:
        data.pop(entry)

    # Write back to the JSON file
    with open(activemessagesids_path, "w") as file:
        json.dump(data, file, indent=4)


def format_mos(user_roles, mos_roles):
    user_mos_roles = []
    for user_role in user_roles:
        if user_role.name in mos_roles:
            user_mos_roles.append(user_role.name)

    if not user_mos_roles:
        return "N/A"

    return "{}".format(", ".join(user_mos_roles))


def format_time_elapsed(date_str):
    if not date_str:
        return "N/A"

    # Parse YYYY-MM-DD format
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Calculate time difference
    today = date.today()
    delta = today - date_obj

    # Format based on elapsed time
    if delta.days > 365:
        return (
            f"{delta.days // 365}y" + f" {(delta.days % 365) % 30}m"
            if delta.days % 365 > 0
            else ""
        )
    elif delta.days > 30:
        return (
            f"{delta.days // 30}m" + f" {(delta.days % 30)}d"
            if delta.days % 30 > 0
            else ""
        )
    elif delta.days > 0:
        return f"{delta.days}d"
    else:
        return "Today"


def list_active_mods(serverconfig_path):
    # Check if the file exists
    if not Path(serverconfig_path).is_file():
        print(f"File {serverconfig_path} does not exist.")
        return []

    # Read the JSON file
    data = {}
    with open(serverconfig_path, "r") as file:
        data = json.load(file)

    # Check if the file is empty
    if not data:
        print(f"File {serverconfig_path} is empty.")
        return []

    # Check if the expected keys are present
    if "game" not in data or "mods" not in data["game"]:
        print(f"File {serverconfig_path} does not contain the expected structure.")
        return []

    # Check if mods is a list
    if not isinstance(data["game"]["mods"], list):
        print(f"File {serverconfig_path} does not contain a list of mods.")
        return []

    # Reading the active mods
    active_mods = []
    for mod in data["game"]["mods"]:
        active_mods.append(mod["name"])

    return active_mods


def list_active_players(serverstats_path):
    # Check if the file exists
    if not Path(serverstats_path).is_file():
        print(f"File {serverstats_path} does not exist.")
        return []

    # Read the JSON file
    data = {}
    with open(serverstats_path, "r") as file:
        data = json.load(file)

    # Check if the file is empty
    if not data:
        print(f"File {serverstats_path} is empty.")
        return []

    # Check if the expected keys are present
    if "connected_players" not in data:
        print(f"File {serverstats_path} does not contain the expected structure.")
        return []

    # Check if connected_players is a dictionary
    if not isinstance(data["connected_players"], dict):
        print(
            f"File {serverstats_path} does not contain a dictionary of connected players."
        )
        return []

    # Reading the active players
    active_players = []
    for player in data["connected_players"].values():
        active_players.append(player)

    return active_players


# Add player bohemia id to a given group (Green, Chalk, ...)
def add_player_to_playersgroups(playersgroups_path, group_name, value):
    """
    Adds a player to a specified group in a JSON file containing player groups.

    If the file does not exist, it will be created. If the file contains invalid JSON,
    it will be backed up and a new file will be created. The function ensures that the
    player is not added to the group more than once.

    Args:
        playersgroups_path (str or Path): Path to the JSON file storing player groups.
        group_name (str): The name of the group to add the player to.
        value (Any): The player value to add to the group.

    Raises:
        OSError: If there is an error reading or writing the file.
    """
    path = Path(playersgroups_path)

    try:
        with path.open("r") as file:
            data = json.load(file)
    except FileNotFoundError:
        log.error(f"File {path} does not exist. Creating a new one.")
        data = {}
    except json.JSONDecodeError:
        log.error(f"File {path} is not a valid JSON. Creating a new one.")
        backup_path = path.with_suffix(f"{path.suffix}.{int(time.time())}.bak")
        os.rename(path, backup_path)
        data = {}

    if value not in data.get(group_name, []):
        data.setdefault(group_name, []).append(value)

    with path.open("w") as file:
        json.dump(data, file, indent=4)

    log.info(f"Player {value} added to group {group_name} in {path}.")


# Remove player bohemia id from a given group (Green, Chalk, ...)
def remove_player_from_playersgroups(playersgroups_path, group_name, value):
    """
    Removes a player from a specified group in a JSON file containing player groups.

    Args:
        playersgroups_path (str or Path): Path to the JSON file storing player groups.
        group_name (str): The name of the group from which to remove the player.
        value (Any): The player value to remove from the group.

    Behavior:
        - If the file does not exist, logs an error and creates a new empty data structure.
        - If the file contains invalid JSON, logs an error, backs up the corrupted file, and creates a new empty data structure.
        - Removes the specified player from the group if present.
        - Writes the updated data back to the file.
    """
    path = Path(playersgroups_path)

    try:
        with path.open("r") as file:
            data = json.load(file)
    except FileNotFoundError:
        log.error(f"File {path} does not exist. Creating a new one.")
        data = {}
    except json.JSONDecodeError:
        log.error(f"File {path} is not a valid JSON. Creating a new one.")
        backup_path = path.with_suffix(f"{path.suffix}.{int(time.time())}.bak")
        os.rename(path, backup_path)
        data = {}

    if value in data.get(group_name, []):
        data[group_name].remove(value)

    with path.open("w") as file:
        json.dump(data, file, indent=4)

    log.info(f"Player {value} removed from group {group_name} in {path}.")


def add_mod_to_serverconfig(serverconfig_path, mod_id, mod_name, mod_version):
    # Check if the file exists
    if not Path(serverconfig_path).is_file():
        print(f"File {serverconfig_path} does not exist.")
        return

    # Read the JSON file
    data = {}
    with open(serverconfig_path, "r") as file:
        data = json.load(file)

    # Check if the file is empty
    if not data:
        print(f"File {serverconfig_path} is empty.")
        return

    # Check if the expected keys are present
    if "game" not in data or "mods" not in data["game"]:
        print(f"File {serverconfig_path} does not contain the expected structure.")
        return

    data["game"]["mods"].append(
        {
            "modId": mod_id,
            "name": mod_name,
            "version": mod_version,
        }
    )

    # Write back to the JSON file
    with open(serverconfig_path, "w") as file:
        json.dump(data, file, indent=4)


def update_mod_version_in_serverconfig(serverconfig_path, mod_id, new_version):
    # Check if the file exists
    if not Path(serverconfig_path).is_file():
        print(f"File {serverconfig_path} does not exist.")
        return

    # Read the JSON file
    data = {}
    with open(serverconfig_path, "r") as file:
        data = json.load(file)

    # Check if the file is empty
    if not data:
        print(f"File {serverconfig_path} is empty.")
        return

    # Check if the expected keys are present
    if "game" not in data or "mods" not in data["game"]:
        print(f"File {serverconfig_path} does not contain the expected structure.")
        return

    # Update the mod version
    for mod in data["game"]["mods"]:
        if mod["modId"] == mod_id:
            mod["version"] = new_version
            break

    # Write back to the JSON file
    with open(serverconfig_path, "w") as file:
        json.dump(data, file, indent=4)


def remove_mod_from_serverconfig(serverconfig_path, mod_id):
    # Check if the file exists
    if not Path(serverconfig_path).is_file():
        print(f"File {serverconfig_path} does not exist.")
        return

    # Read the JSON file
    data = {}
    with open(serverconfig_path, "r") as file:
        data = json.load(file)

    # Check if the file is empty
    if not data:
        print(f"File {serverconfig_path} is empty.")
        return

    # Check if the expected keys are present
    if "game" not in data or "mods" not in data["game"]:
        print(f"File {serverconfig_path} does not contain the expected structure.")
        return

    # Update the mod version
    index = -1
    for i, mod in enumerate(data["game"]["mods"]):
        if mod["modId"] == mod_id:
            index = i
            break

    if index != -1:
        data["game"]["mods"].pop(index)

    # Write back to the JSON file
    with open(serverconfig_path, "w") as file:
        json.dump(data, file, indent=4)


def get_channel(bot, channel_id):
    try:
        channel = bot.get_channel(channel_id)
        return channel
    except discord.NotFound:
        print(f"Channel with ID {channel_id} not found.")
        return None
    except discord.Forbidden:
        print(f"Permission denied to access channel {channel_id}.")
        return None


async def send_embed(channel, title=None, description=None, color=discord.Color.blue()):
    embed = discord.Embed(title=title, description=description, color=color)

    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Failed to send embed message: {e}")
