import subprocess
import json
from datetime import datetime, date
from pathlib import Path

import discord


def is_port_listening(port=2001):
    result = subprocess.run(
        ["ss", "-tuln", f"sport = :{port}"], capture_output=True, text=True
    )
    return any(f":{port}" in line for line in result.stdout.splitlines())


# CPU and memory usage
def get_server_utilization():
    # Get CPU, memory, and disk usage
    cpu = float(
        subprocess.check_output(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", shell=True
        )
        .decode()
        .strip()
    )
    memory = float(
        subprocess.check_output(
            "free -m | grep Mem | awk '{print $3/$2 * 100.0}'", shell=True
        )
        .decode()
        .strip()
    )
    disk = float(
        subprocess.check_output("df -h / | awk 'NR==2 {print $5}'", shell=True)
        .decode()
        .strip()[:-1]
    )

    return cpu, memory, disk


# Restart the gameserver
def restart_gameserver():
    subprocess.run(["sudo", "systemctl", "restart", "arma-reforger-server"], check=True)


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
        return ""

    return "[{}]".format(", ".join(user_mos_roles))


def format_time_elapsed(date_str):
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
        return "today"


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


def add_player_to_playersgroups(playersgroups_path, group_name, value):
    # Check if the file exists
    if not Path(playersgroups_path).is_file():
        print(f"File {playersgroups_path} does not exist. Creating a new file.")

        # Create the file if it doesn't exist
        with open(playersgroups_path, "w") as file:
            json.dump({}, file, indent=4)

        raise FileNotFoundError(
            f"File {playersgroups_path} does not exist. A new file has been created."
        )

    # Read the JSON file
    data = {}
    with open(playersgroups_path, "r") as file:
        data = json.load(file)

    if group_name not in data:
        data[group_name] = []

    if value not in data[group_name]:
        data[group_name].append(value)

    with open(playersgroups_path, "w") as file:
        json.dump(data, file, indent=4)


def remove_player_from_playersgroups(playersgroups_path, group_name, value):
    # Check if the file exists
    if not Path(playersgroups_path).is_file():
        print(f"File {playersgroups_path} does not exist. Creating a new file.")

        # Create the file if it doesn't exist
        with open(playersgroups_path, "w") as file:
            json.dump({}, file, indent=4)

        raise FileNotFoundError(
            f"File {playersgroups_path} does not exist. A new file has been created."
        )

    # Read the JSON file
    data = {}
    with open(playersgroups_path, "r") as file:
        data = json.load(file)

    if group_name in data and value in data[group_name]:
        data[group_name].remove(value)

        with open(playersgroups_path, "w") as file:
            json.dump(data, file, indent=4)


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
