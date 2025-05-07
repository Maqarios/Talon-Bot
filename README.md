# Talon Bot

A Discord bot for Red Talon Special Operations Group (RTSOG) server management, created by May-Day. This bot integrates Discord community management with Arma Reforger game server administration.

## Features

*   **Server Monitoring**:
    *   Real-time VPS metrics (CPU, Memory, Disk).
    *   Game server status (online/offline).
    *   Active player list.
    *   Active mods list.
*   **Discord Management**:
    *   User registration and tracking.
    *   Team and role management.
    *   Misconduct tracking.
*   **Game Server Administration**:
    *   Server restart.
    *   Scenario changes.
    *   Loadout management.
    *   Bohemia ID linking.

## Commands

### General

*   `/ping`: Checks bot responsiveness.
*   `/privacy`: Displays the privacy policy.

### User Management

*   `/register`: Registers a user in the database.
*   `/register_user`: (Admin) Registers another user.
*   `/delete_user`: (Admin) Deletes a user from the database.
*   `/change_user_team`: (Admin) Changes a user's team.
*   `/show_user_team_logs`: (Admin) Shows a user's team logs.
*   `/add_misconduct`: (Admin) Adds a misconduct record to a user.
*   `/show_misconducts`: (Admin) Shows a user's misconduct records.
*   `/link_user_bohemia_id`: (Admin) Links a user's Bohemia ID.

### Server Management

*   `/restart_gameserver`: (Admin) Restarts the game server.
*   `/change_scenario`: (Admin) Changes the active scenario.

### MOS Management

*   `/delete_user_loadout`: (Admin) Deletes a user's loadout.
*   `/start_mos_check`: (Admin) Copies a user's loadout for inspection.
*   `/stop_mos_check`: (Admin) Restores the admin's original loadout.

## Database

The bot uses a SQLite database to store user data, team logs, and misconduct records.

### Tables

*   `users`: Stores user information.
*   `team_logs`: Stores team assignment history.
*   `misconduct_logs`: Stores misconduct records.

### User Table

| Column            | Type    | Description                               |
| :---------------- | :------ | :---------------------------------------- |
| `discord_id`      | BIGINT  | Discord user ID (primary key)             |
| `discord_username`| TEXT    | Discord username                          |
| `discord_displayname` | TEXT    | Discord display name                      |
| `status`          | TEXT    | User status (Active, Inactive, Banned, Retired) |
| `team`            | TEXT    | Assigned team                             |
| `joined`          | DATE    | Date the user joined the team             |
| `bohemia_id`      | TEXT    | Bohemia Interactive ID                    |

### Team Logs Table

| Column              | Type    | Description                           |
| :------------------ | :------ | :------------------------------------ |
| `id`                | INTEGER | Primary key                           |
| `instigator_discord_id` | BIGINT  | Discord ID of the admin who made the change |
| `target_discord_id`   | BIGINT  | Discord ID of the affected user       |
| `team`              | TEXT    | Assigned team                         |
| `details`           | TEXT    | Details of the change                   |
| `timestamp`         | DATETIME| Timestamp of the change               |

### Misconduct Logs Table

| Column              | Type    | Description                               |
| :------------------ | :------ | :---------------------------------------- |
| `id`                | INTEGER | Primary key                               |
| `instigator_discord_id` | BIGINT  | Discord ID of the admin who added the record |
| `target_discord_id`   | BIGINT  | Discord ID of the user with misconduct    |
| `victim_discord_id`   | BIGINT  | Discord ID of the victim (if any)         |
| `category`          | TEXT    | Misconduct category                       |
| `type`              | TEXT    | Specific type of misconduct               |
| `details`           | TEXT    | Details of the incident                   |
| `severity`          | INTEGER | Severity level (0-2)                      |
| `timestamp`         | DATETIME| Timestamp of the record                   |

## Technical Details

*   **Language**: Python 3.x
*   **Libraries**:
    *   discord.py
    *   watchdog
*   **File Watchers**: Monitors server stats and config files for changes.
*   **Caching**: Caches player data for faster lookups.
*   **Centralized Configuration**: Channel IDs and other settings are stored in `config.py`.

## Setup

1.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```
2.  Configure the bot:

    *   Set the bot token in `config.py`.
    *   Configure channel IDs in `config.py`.
    *   Set the correct paths for server stats and config files.
3.  Run the bot:

    ```bash
    python bot.py
    ```

## Configuration

### config.py

This file contains all the configuration settings for the bot.

*   `BOT_TOKEN`: The bot's token.  **Important**: Use environment variables instead of storing the token directly in the file.
*   `ADMIN_IDS`: A list of Discord user IDs with admin privileges.
*   `CHANNEL_IDS`: A dictionary of channel IDs for different functions.
*   `GAMESERVER_PORT`: The port the game server is listening on.
*   `SERVERSTATS_PATH`: The path to the server stats file.
*   `PROFILE_DIR_PATH`: The path to the Arma Reforger profile directory.
*   `ACTIVEMESSAGESIDS_PATH`: The path to the active messages ID file.
*   `TEAMS`: A dictionary of team names and role IDs.
*   `MISCONDUCT_CATEGORIES`: A dictionary of misconduct categories and types.
*   `USER_DB_PATH`: The path to the SQLite database file.
*   `SLEEP_TIME`: The time to wait before retrying a failed operation.
*   `SERVERCONFIG_PATH`: The path to the server configuration file.
*   `SCENARIONS_IDS`: A list of scenario IDs.

### active\_messages\_ids.json

This file stores the IDs of active messages that the bot manages.

## Cogs

The bot's functionality is organized into cogs.

*   `serverconfig.py`: Contains commands for managing the server configuration.
*   `mos.py`: Contains commands for managing MOS and loadouts.

## Utils

The `utils` directory contains helper functions and classes.

*   `utils.py`: Contains utility functions.
*   `file_watchers.py`: Contains file watchers for server stats and config files.
*   `database_managers.py`: Contains database management classes.
*   `cache.py`: Contains caching mechanisms.
*   `active_messages.py`: Contains functions for managing active messages.

## Next Steps

*   Implement input validation for commands.
*   Implement rate limiting.
*   Implement proper logging.
*   Add unit tests.