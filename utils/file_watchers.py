import json
import os
import threading
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils.loggers import get_logger

log = get_logger(__name__)


class GenericFileWatcher(FileSystemEventHandler):
    def __init__(self, filepath):
        self.filepath = filepath

    def _initiate_or_reset_data(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def _load_file(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def _sanitize_data(self, data):
        return data

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == os.path.abspath(self.filepath):
            data = self._load_file()
            if data:
                self._sanitize_data(data)
            else:
                self._initiate_or_reset_data()

    def start(self):
        observer = Observer()
        observer.schedule(
            self,
            path=os.path.dirname(os.path.abspath(self.filepath)) or ".",
            recursive=False,
        )
        observer.start()
        threading.Thread(target=observer.join, daemon=True).start()


class ServerAdminToolsStatsFileWatcher(GenericFileWatcher):
    def __init__(self, filepath):
        super().__init__(filepath)

        # Define structure of the data
        self.fields = [
            "registered_systems",
            "registered_entities",
            "registered_groups",
            "uptime_seconds",
            "fps",
            "registered_tasks",
            "registered_vehicles",
            "ai_characters",
            "players",
            "updated",
            "connected_players",
            "events",
        ]

        # Initiate the empty data
        self._initiate_or_reset_data()

        # Read initial file contents
        data = self._load_file()
        if data:
            self._sanitize_data(data)

    def _initiate_or_reset_data(self):
        self.registered_systems = -1
        self.registered_entities = -1
        self.registered_groups = -1
        self.uptime_seconds = -1
        self.fps = -1
        self.registered_tasks = -1
        self.registered_vehicles = -1
        self.ai_characters = -1
        self.players = -1
        self.updated = -1
        self.connected_players = {}
        self.events = {}

    def _load_file(self):
        if not Path(self.filepath).is_file():
            log.error(f"File {self.filepath} does not exist.")
            return {}

        try:
            with open(self.filepath, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            log.error(f"File {self.filepath} is not a valid JSON file.")
            return {}

    def _sanitize_data(self, data):
        for field in self.fields:
            if field in data:
                setattr(self, field, data[field])

        # Sort connected players by name
        self.connected_players = dict(
            sorted(self.connected_players.items(), key=lambda x: x[1].lower())
        )


class ServerConfigFileWatcher(GenericFileWatcher):
    def __init__(self, filepath):
        super().__init__(filepath)
        self.game = ServerConfigGame()

        # Define structure of the data
        self.fields = [
            "bindAddress",
            "bindPort",
            "publicAddress",
            "publicPort",
            "game",
        ]

        # Initiate the empty data
        self._initiate_or_reset_data()

        # Read initial file contents
        data = self._load_file()
        if data:
            self._sanitize_data(data)

    def _initiate_or_reset_data(self):
        # Base
        self.bindAddress = ""
        self.bindPort = -1
        self.publicAddress = ""
        self.publicPort = -1

        # game
        self.game._initiate_or_reset_data()

    def _load_file(self):
        if not Path(self.filepath).is_file():
            log.error(f"File {self.filepath} does not exist.")
            return {}

        try:
            with open(self.filepath, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            log.error(f"File {self.filepath} is not a valid JSON file.")
            return {}

    def _sanitize_data(self, data):
        for field in self.fields:
            if field in data:
                if field == "game":
                    self.game._sanitize_data(data[field])
                else:
                    setattr(self, field, data[field])


class ServerConfigGame:
    def __init__(self):
        # Define structure of the data
        self.fields = [
            "name",
            "password",
            "scenarioId",
            "maxPlayers",
            "mods",
        ]

        self._initiate_or_reset_data()

    def _initiate_or_reset_data(self):
        self.name = ""
        self.password = ""
        self.scenarioId = ""
        self.maxPlayers = -1
        self.mods = []
        self.searchable_mods = {}

    def _sanitize_data(self, data):
        for field in self.fields:
            if field in data:
                setattr(self, field, data[field])

        # Sort mods by name
        self.mods = sorted(self.mods, key=lambda x: x["name"].lower())

        # Create searchable_mods dictionary
        self.searchable_mods = {}
        for mod in self.mods:
            mod_id = mod["modId"]
            self.searchable_mods[mod_id] = {
                "name": mod["name"],
                "version": mod["version"],
            }
