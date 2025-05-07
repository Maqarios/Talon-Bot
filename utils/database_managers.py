import sqlite3
import config


class UserDatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            discord_id BIGINT PRIMARY KEY, 
            discord_username TEXT NOT NULL,
            discord_displayname TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Banned', 'Retired')),
            team TEXT NOT NULL DEFAULT 'Unassigned' CHECK (team IN ('Unassigned', 'Green Team', 'Chalk Team', 'Red Section', 'Grey Section', 'Black Section', 'Red Talon')),
            joined DATE NOT NULL DEFAULT (date('now', 'localtime')),
            bohemia_id TEXT UNIQUE DEFAULT NULL )
        """
        )

        conn.commit()
        conn.close()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        return conn, conn.cursor()

    def create(self, id, username, display_name):
        conn, cursor = self.get_connection()
        cursor.execute(
            "INSERT OR IGNORE INTO users (discord_id, discord_username, discord_displayname) VALUES (?, ?, ?)",
            (id, username, display_name),
        )
        conn.commit()
        conn.close()

    def read(self, id):
        conn, cursor = self.get_connection()
        cursor.execute("SELECT * FROM users WHERE discord_id = ?", (id,))
        result = cursor.fetchone()
        conn.close()

        return result

    def read_discord_displayname(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "SELECT discord_displayname FROM users WHERE discord_id = ?", (id,)
        )
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def read_team(self, id):
        conn, cursor = self.get_connection()
        cursor.execute("SELECT team FROM users WHERE discord_id = ?", (id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def read_bohemia_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute("SELECT bohemia_id FROM users WHERE discord_id = ?", (id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def read_by_bohemia_id(self, bohemia_id):
        conn, cursor = self.get_connection()
        cursor.execute("SELECT * FROM users WHERE bohemia_id = ?", (bohemia_id,))
        result = cursor.fetchone()
        conn.close()

        return result

    def update_team(self, id, team):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE users SET team = ? WHERE discord_id = ?",
            (team, id),
        )
        conn.commit()
        conn.close()

    def update_status(self, id, status):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE users SET status = ? WHERE discord_id = ?",
            (status, id),
        )
        conn.commit()
        conn.close()

    def update_bohemia_id(self, id, bohemia_id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE users SET bohemia_id = ? WHERE discord_id = ?",
            (bohemia_id, id),
        )
        conn.commit()
        conn.close()

    def delete(self, id):
        conn, cursor = self.get_connection()
        cursor.execute("DELETE FROM users WHERE discord_id = ?", (id,))
        conn.commit()
        conn.close()

    def reset_joined(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE users SET joined = date('now', 'localtime') WHERE discord_id = ?",
            (id,),
        )
        conn.commit()
        conn.close()

    def get_users_for_active_message(self):
        conn, cursor = self.get_connection()
        cursor.execute(
            "SELECT discord_displayname, status, team, joined FROM users ORDER BY joined"
        )
        users = cursor.fetchall()
        conn.close()
        return users


class RoleLogDatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS team_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instigator_discord_id BIGINT NOT NULL,
            target_discord_id BIGINT NOT NULL,
            team TEXT NOT NULL CHECK (team IN ('Unassigned', 'Green Team', 'Chalk Team', 'Red Section', 'Grey Section', 'Black Section', 'Red Talon')),
            details TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        conn.commit()
        conn.close()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        return conn, conn.cursor()

    def create(self, instigator_id, target_id, team, details):
        conn, cursor = self.get_connection()
        cursor.execute(
            "INSERT INTO team_logs (instigator_discord_id, target_discord_id, team, details) VALUES (?, ?, ?, ?)",
            (instigator_id, target_id, team, details),
        )
        conn.commit()
        conn.close()

    def read_by_target_discord_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute("SELECT * FROM team_logs WHERE target_discord_id = ?", (id,))
        result = cursor.fetchall()
        conn.close()

        return result

    def mark_as_deleted_by_instigator_discord_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE team_logs SET instigator_discord_id = -1 WHERE instigator_discord_id = ?",
            (id,),
        )
        conn.commit()
        conn.close()

    def mark_as_deleted_by_target_discord_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE team_logs SET target_discord_id = -1 WHERE target_discord_id = ?",
            (id,),
        )
        conn.commit()
        conn.close()


class MisconductLogDatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS misconduct_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instigator_discord_id BIGINT NOT NULL,
            target_discord_id BIGINT NOT NULL,
            victim_discord_id BIGINT,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            details TEXT NOT NULL,
            severity INT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        conn.commit()
        conn.close()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        return conn, conn.cursor()

    def create(
        self, instigator_id, target_id, victim_id, category, type, details, severity
    ):
        conn, cursor = self.get_connection()
        cursor.execute(
            "INSERT INTO misconduct_logs (instigator_discord_id, target_discord_id, victim_discord_id, category, type, details, severity) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (instigator_id, target_id, victim_id, category, type, details, severity),
        )
        conn.commit()
        conn.close()

    def read_by_target_discord_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "SELECT * FROM misconduct_logs WHERE target_discord_id = ?", (id,)
        )
        result = cursor.fetchall()
        conn.close()

        return result

    def mark_as_deleted_by_instigator_discord_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE misconduct_logs SET instigator_discord_id = -1 WHERE instigator_discord_id = ?",
            (id,),
        )
        conn.commit()
        conn.close()

    def mark_as_deleted_by_target_discord_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE misconduct_logs SET target_discord_id = -1 WHERE target_discord_id = ?",
            (id,),
        )
        conn.commit()
        conn.close()

    def mark_as_deleted_by_victim_discord_id(self, id):
        conn, cursor = self.get_connection()
        cursor.execute(
            "UPDATE misconduct_logs SET victim_discord_id = -1 WHERE victim_discord_id = ?",
            (id,),
        )
        conn.commit()
        conn.close()


USERS_DBM = UserDatabaseManager(config.USER_DB_PATH)
ROLE_LOGS_DBM = RoleLogDatabaseManager(config.USER_DB_PATH)
MISCONDUCT_LOGS_DBM = MisconductLogDatabaseManager(config.USER_DB_PATH)
