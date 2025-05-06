# Talon Bot

A Discord bot created by May-Day for Red Talon Special Operations Group (RTSOG) Server Management. This bot provides comprehensive functionality for managing both a Discord community and an Arma Reforger game server.

## Table of Contents
- [Features Overview](#features-overview)
- [Server Management Commands](#server-management-commands)
- [User Management System](#user-management-system)
- [Team and Role System](#team-and-role-system)
- [Misconduct Tracking System](#misconduct-tracking-system)
- [Game Integration](#game-integration)
- [Technical Architecture](#technical-architecture)
- [Setup and Configuration](#setup-and-configuration)

## Features Overview

### VPS and Game Server Monitoring
- Real-time performance metrics (CPU, Memory, Disk)
- Server status tracking (online/offline)
- Active player monitoring and listing
- Automatic mod list compilation

### Discord Server Management
- User registration and tracking
- Role assignment and team management
- Misconduct tracking and documentation
- Self-service team enrollment

### Game Server Management
- Server restart capability
- Scenario/mission changes
- Loadout verification system
- Player BohemiaID integration

## Server Management Commands

### Basic Commands
- `/ping`: Confirms bot is responsive (responds with "pong")
- `/privacy`: Displays data usage policy in a formatted embed

### Server Administration
- `/restart_gameserver`: Safely restarts the Arma Reforger server
- `/change_scenario`: Changes the active mission on the game server

## User Management System

### Registration
- **Automatic**: Users are registered when joining the server
- **Manual**: `/register` for self-registration
- **Admin**: `/register_user` for admin-initiated registration
- **Removal**: `/delete_user` for complete data removal (GDPR compliant)

### User Database Structure
| Field | Type | Description |
|-------|------|-------------|
| `discord_id` | BIGINT (PK) | Unique Discord identifier |
| `discord_username` | TEXT | User's Discord username |
| `discord_displayname` | TEXT | Display name on the server |
| `status` | TEXT | 'Active', 'Inactive', 'Banned', or 'Retired' |
| `team` | TEXT | Assigned operational team |
| `joined` | DATE | When user joined their current team |
| `bohemia_id` | TEXT (UNIQUE) | Game identity link (can be NULL) |

### Lifecycle Management
- **Join Handling**: Auto-registration with 'Active' status
- **Rejoin Handling**: Status restoration and join date reset
- **Leave Tracking**: Auto-update to 'Inactive' status
- **Ban System**: Status-based with record preservation

## Team and Role System

### Team Structure
The bot manages members across multiple operational teams:
- Unassigned (default)
- Green Team
- Chalk Team
- Red Section
- Grey Section
- Black Section
- Red Talon (leadership)

### Team Management
- `/change_user_team`: Admin command to reassign users between teams
- `/show_user_team_logs`: View complete history of team changes
- Reaction-based team joining (Green Team enrollment via 🟩 reaction)

### Team Logs Database
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER (PK) | Auto-incrementing ID |
| `instigator_discord_id` | BIGINT | Admin who made the change |
| `target_discord_id` | BIGINT | User affected by the change |
| `team` | TEXT | Team assigned in this change |
| `details` | TEXT | Context or reason for change |
| `timestamp` | DATETIME | When change was recorded |

## Misconduct Tracking System

### Misconduct Documentation
- `/add_misconduct`: Records infractions with detailed categorization
- `/show_misconducts`: Displays complete misconduct history for a user

### Categorization System
Misconduct is organized into categories with specific types:
- Operational Violations (MOS Breach, AWOL, etc.)
- Combat Discipline Violations (Team Killing, Friendly Fire)
- Cheating & Exploits
- Behavioral Misconduct
- Security & Intelligence Violations
- Leadership & Admin Violations
- Mission Integrity Violations

### Severity Levels
- **Green (0)**: Minor infractions
- **Yellow (1)**: Significant issues
- **Red (2)**: Severe violations

### Misconduct Database
| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER (PK) | Auto-incrementing ID |
| `instigator_discord_id` | BIGINT | Admin recording the misconduct |
| `target_discord_id` | BIGINT | User who committed the violation |
| `victim_discord_id` | BIGINT (NULL) | User affected if applicable |
| `category` | TEXT | General category of misconduct |
| `type` | TEXT | Specific violation type |
| `details` | TEXT | Context and description |
| `severity` | INTEGER | Severity level (0-2) |
| `timestamp` | DATETIME | When recorded |

## Game Integration

### Bohemia ID Linking
- `/link_user_bohemia_id`: Links Discord users to in-game identities
- Intelligent autocomplete from detected unlinked players
- Automatic player categorization (known/unknown)

### MOS and Loadout Management
- `/delete_user_loadout`: Removes saved loadouts for a user
- `/start_mos_check`: Copies target's loadout to admin for inspection
- `/stop_mos_check`: Restores admin's original loadout after inspection

### Active Monitoring
- Real-time player list with game connection status
- Server status tracking with visual indicators
- Active mod list compilation and display

## Technical Architecture

### File Watchers
- **ServerAdminToolsStatsFileWatcher**: Monitors game server statistics file
- **ServerConfigFileWatcher**: Tracks configuration changes

### Active Message System
The bot maintains several self-updating status messages:
- Server utilization metrics (CPU/Memory/Disk)
- Team membership roster with tenure
- Active player list with connection status
- Mod list for server configuration

### Database Managers
- **UserDatabaseManager**: Handles user record operations
- **RoleLogDatabaseManager**: Manages team change history
- **MisconductLogDatabaseManager**: Tracks misconduct records

### Player Caching System
- Maintains lists of known and unknown players
- Facilitates quick lookups and autocompletion
- Updates dynamically as players are detected or linked

### Event Handling
The bot responds automatically to Discord events:
- Member joins/leaves
- Button interactions for refreshing data
- Reaction-based role assignments

## Setup and Configuration

### Requirements
- Python 3.8+
- discord.py 2.5.2+
- watchdog 6.0.0+
- Access to a Linux VPS (for server monitoring)

### Configuration Files
- **config.py**: Contains bot token, server paths, and role IDs
- **active_messages_ids.json**: Tracks message IDs for updating

### Directory Structure
- **/utils**: Helper functions and utility classes
- **/cogs**: Command modules and feature sets
- **/dbs**: Database files and storage

### Deployment
1. Clone the repository
2. Install dependencies from requirements.txt
3. Configure token and paths in config.py
4. Run bot.py to start the system

```bash
# Install dependencies
pip install -r requirements.txt

# Start the bot
python bot.py