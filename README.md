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
### Integration
`/link_user_bohemia_id`: Links a player's in-game Bohemia ID to their Discord account. Admin-only command that accepts a Discord user and in-game name parameters. Features an intelligent caching system that categorizes players as either "known" (already registered in database) or "unknown" (detected on the server but not yet linked to Discord). The autocomplete functionality suggests names from currently unknown players detected on the game server, eliminating manual entry errors. When a player is linked, they move from the "unknown" cache to the "known" cache, ensuring proper cross-platform tracking between Discord and in-game environments.
### Extras
`/ping`: Simple command that responds with "pong" to confirm the bot is online and responsive. Response is ephemeral and only visible to the command user.

`/privacy`: Displays the bot's privacy policy detailing what data is collected (Discord ID, username, display name, Bohemia ID), how it's used, data retention policies, and user rights. The information appears in an organized embed that's only visible to the command user.

