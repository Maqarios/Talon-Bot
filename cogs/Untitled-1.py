
class UserDatabaseManager2:
    def __init__(self, db_filepath: str):
        self.db_filepath = db_filepath

        self.conn = None
        self.cursor = None

        self._connect()
        self._initialize_database()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_filepath)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def _initialize_database(self):
        try:
            self.cursor.execute(
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
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise

    def create(self, id, username, display_name):
        try:
            self.cursor.execute(
                "INSERT INTO users (discord_id, discord_username, discord_displayname) VALUES (?, ?, ?)",
                (id, username, display_name),
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating user: {e}")
            raise

    def read(self, id):
        try:
            self.cursor.execute("SELECT * FROM users WHERE discord_id = ?", (id,))
            result = self.cursor.fetchone()
            return result
        except sqlite3.Error as e:
            print(f"Error reading user: {e}")
            raise

    def read_discord_displayname(self, id):
        try:
            self.cursor.execute(
                "SELECT discord_displayname FROM users WHERE discord_id = ?", (id,)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error reading discord display name: {e}")
            raise

    def read_team(self, id):
        try:
            self.cursor.execute("SELECT team FROM users WHERE discord_id = ?", (id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error reading team: {e}")
            raise

    def read_bohemia_id(self, id):
        try:
            self.cursor.execute(
                "SELECT bohemia_id FROM users WHERE discord_id = ?", (id,)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error reading Bohemia ID: {e}")
            raise

    def read_by_bohemia_id(self, bohemia_id):
        try:
            self.cursor.execute(
                "SELECT * FROM users WHERE bohemia_id = ?", (bohemia_id,)
            )
            result = self.cursor.fetchone()
            return result
        except sqlite3.Error as e:
            print(f"Error reading user by Bohemia ID: {e}")
            raise

    def update_team(self, id, team):
        try:
            self.cursor.execute(
                "UPDATE users SET team = ? WHERE discord_id = ?",
                (team, id),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating team: {e}")
            raise

    def update_status(self, id, status):
        try:
            self.cursor.execute(
                "UPDATE users SET status = ? WHERE discord_id = ?",
                (status, id),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating status: {e}")
            raise

    def update_bohemia_id(self, id, bohemia_id):
        try:
            self.cursor.execute(
                "UPDATE users SET bohemia_id = ? WHERE discord_id = ?",
                (bohemia_id, id),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating Bohemia ID: {e}")
            raise

    def delete(self, id):
        try:
            self.cursor.execute("DELETE FROM users WHERE discord_id = ?", (id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error deleting user: {e}")
            raise

    def reset_joined(self, id):
        try:
            self.cursor.execute(
                "UPDATE users SET joined = date('now', 'localtime') WHERE discord_id = ?",
                (id,),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error resetting joined date: {e}")
            raise

    def get_users_for_active_message(self):
        try:
            self.cursor.execute(
                "SELECT discord_displayname, status, team, joined FROM users ORDER BY joined"
            )
            users = self.cursor.fetchall()
            return users
        except sqlite3.Error as e:
            print(f"Error fetching users for active message: {e}")
            raise

    def _disconnect(self):
        if self.conn:
            self.conn.close()

