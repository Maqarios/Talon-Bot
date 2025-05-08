# Discord Bot for Arma Reforger Community

This Discord bot is designed to enhance the Arma Reforger community experience by providing various utilities, moderation tools, and server status updates.

## Features

-   **User Management:**
    -   Register new users and manage their roles.
    -   Track user activity and team assignments.
    -   Link Bohemia IDs to Discord users for in-game integration.

-   **Moderation Tools:**
    -   Log and manage user misconduct with categories and severity levels.
    -   Commands to view user-specific logs.

-   **Server Status:**
    -   Display real-time server utilization (CPU, Memory, Disk).
    -   Monitor active players on the game server.
    -   Track active mods.

-   **Team Management:**
    -   Assign users to different teams with corresponding Discord roles.
    -   Display team compositions and member join dates.

-   **Configuration:**
    -   Easily configurable through a `config.py` file.
    -   File watchers for automatic updates on server configuration changes.

## Setup

1.  **Prerequisites:**
    -   Python 3.6+
    -   `pip` package manager

2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    -   Create a `config.py` file based on the provided example.
    -   Fill in the necessary tokens, IDs, and file paths.

4.  **Database Setup:**
    -   The bot uses SQLite for user and log data. Ensure the database file path is correctly configured in `config.py`.

5.  **Run the Bot:**

    ```bash
    python bot.py
    ```

## File Structure

```
DiscordBot/
├── bot.py                  # Main bot file
├── config.py               # Configuration settings
├── cogs/                   # Cog files for different functionalities
│   ├── __init__.py
│   ├── misc.py             # Miscellaneous commands (ping, privacy, restart server)
│   ├── user.py             # User management commands (register, delete, misconduct, team management)
│   ├── serverconfig.py     # Server configuration commands (change scenario)
│   └── mos.py              # MOS related commands (loadout management)
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── utils.py            # Helper functions (server status, time formatting)
│   ├── database_managers.py# Database management classes
│   ├── active_messages.py  # Logic for updating active status messages
│   ├── file_watchers.py    # File monitoring for server configuration
│   └── cache.py            # Caching mechanisms
├── dbs/                    # Database files (not tracked by Git)
├── .gitignore              # Specifies intentionally untracked files
├── README.md               # Documentation
└── requirements.txt        # Python dependencies
```

## Cogs

-   **UserCog:** Manages user registration, deletion, misconduct logging, and team assignments.
    -   `/register`: Registers the user in the database.
    -   `/register_user`: Registers a specified user in the database (Admin only).
    -   `/delete_user`: Deletes a specified user from the database (Admin only).
    -   `/add_misconduct`: Adds a misconduct record for a user (Admin only).
    -   `/show_misconducts`: Shows the misconduct logs for a specified user (Admin only).
    -   `/change_user_team`: Changes a user's team (Admin only).
    -   `/show_user_team_logs`: Shows a user's team logs (Admin only).
    -   `/link_user_bohemia_id`: Links a Bohemia ID to a user (Admin only).
-   **MiscCog:** Includes general utility commands such as `ping`, `privacy`, and `restart_gameserver`.
    -   `/ping`: Checks the bot's latency.
    -   `/privacy`: Displays the privacy policy.
    -   `/restart_gameserver`: Restarts the game server (Admin only).
-   **ServerConfigCog:** Allows administrators to change server settings like the scenario ID.
    -   `/change_scenario`: Changes the server scenario (Admin only).
-   **MosCog:** MOS related commands for loadout management.
    -   `/delete_user_loadout`: Deletes the loadout for a specified user (Admin only).
    -   `/start_mos_check`: Copies the loadout from a specified user to the command invoker (Admin only).
    -   `/stop_mos_check`: Restores the original loadout of the command invoker (Admin only).

## Utilities

-   **Database Managers:** Provides classes for interacting with the SQLite database, including user management, role logs, and misconduct logs.
-   **Active Messages:** Manages and updates Discord messages that display dynamic information, such as server status and team compositions.
-   **File Watchers:** Monitors server configuration files for changes and automatically updates bot settings.
-   **Cache:** Caching mechanisms for storing and quickly accessing data, such as Bohemia IDs.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the [MIT License](LICENSE).
