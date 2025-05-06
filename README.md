# Talon Bot
Created by May-Day for Red Talon Special Operatios Group (RTSOG) Server Management.

## Purpose
### Virtual Private Server (VPS) Managemet
- Server Utilization Active Message: Displays real-time VPS resource metrics (CPU, Memory, Disk) with color indicators that change from green to red when resources approach critical thresholds. Includes a refresh button and automatically updates every minute.
### Discord Server Managment
#### User System
##### Database
#### Promotion/Demotion System
#### Misconduct System
##### Database
### Arma Reforger Server Management
#### Priviliges
#### Ban System
### Integrated Commands
`/link_user_bohemia_id`: Links a player's in-game Bohemia ID to their Discord account. Admin-only command that accepts a Discord user and in-game name parameters. Features an intelligent caching system that categorizes players as either "known" (already registered in database) or "unknown" (detected on the server but not yet linked to Discord). The autocomplete functionality suggests names from currently unknown players detected on the game server, eliminating manual entry errors. When a player is linked, they move from the "unknown" cache to the "known" cache, ensuring proper cross-platform tracking between Discord and in-game environments.
#### MOS Management
`/delete_user_loadout`: Admin-only command that permanently deletes a user's saved loadouts from both the Bacon Loadout Editor and the persistent loadout systems. Takes a Discord user parameter and removes the corresponding loadout files associated with their linked Bohemia ID.

`/start_mos_check`: Admin-only command that temporarily copies another user's loadout files to the initiating admin's profile. This enables admins to visually inspect another user's loadout configuration in-game without modifying the original. The command backs up the admin's original loadout files and replaces them with copies of the target user's loadouts.

`/stop_mos_check`: Admin-only command that restores the initiating admin's original loadout files after completing a loadout inspection with `/start_mos_check`. This command removes the temporary target user's loadout files and restores the admin's backed-up loadouts to their original state.

### Extras
`/ping`: Simple command that responds with "pong" to confirm the bot is online and responsive. Response is ephemeral and only visible to the command user.

`/privacy`: Displays the bot's privacy policy detailing what data is collected (Discord ID, username, display name, Bohemia ID), how it's used, data retention policies, and user rights. The information appears in an organized embed that's only visible to the command user.

