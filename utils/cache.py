from utils.database_managers import users_dbm


class ActivePlayersBohemiaIDCache:
    def __init__(self, users_dbm):
        self.users_dbm = users_dbm
        self.cache = {"known": {}, "unknown": {}}

    def get_known_players(self):
        return self.cache["known"]

    def add_known_player(self, player_bohemia_id, player_name):
        self.cache["known"][player_bohemia_id] = player_name

    def remove_known_player(self, player_bohemia_id):
        if player_bohemia_id in self.cache["known"]:
            del self.cache["known"][player_bohemia_id]

    def get_unknown_players(self):
        return self.cache["unknown"]

    def add_unknown_player(self, player_bohemia_id, player_name):
        self.cache["unknown"][player_bohemia_id] = player_name

    def remove_unknown_player(self, player_bohemia_id):
        if player_bohemia_id in self.cache["unknown"]:
            del self.cache["unknown"][player_bohemia_id]

    def handle_player(self, player_bohemia_id, player_name):
        if player_bohemia_id in self.cache["known"]:
            return

        if player_bohemia_id in self.cache["unknown"]:
            return

        if self.users_dbm.read_by_bohemia_id(player_bohemia_id):
            self.add_known_player(player_bohemia_id, player_name)
            return

        self.add_unknown_player(player_bohemia_id, player_name)


ACTIVE_PLAYERS_BOHEMIA_ID_CACHE = ActivePlayersBohemiaIDCache(users_dbm)
