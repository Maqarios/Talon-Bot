import json
import os
import threading
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ServerAdminToolsStatsFileWatcher(FileSystemEventHandler):
    def __init__(self, filepath):
        self.filepath = filepath

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
            print(f"File {self.filepath} does not exist.")
            return {}

        try:
            with open(self.filepath, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"File {self.filepath} is not a valid JSON file.")
            return {}

    def _sanitize_data(self, data):
        for field in self.fields:
            if field in data:
                setattr(self, field, data[field])

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


class ServerConfigFileWatcher(FileSystemEventHandler):
    def __init__(self, filepath):
        self.filepath = filepath
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
            print(f"File {self.filepath} does not exist.")
            return {}

        try:
            with open(self.filepath, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"File {self.filepath} is not a valid JSON file.")
            return {}

    def _sanitize_data(self, data):
        for field in self.fields:
            if field in data:
                if field == "game":
                    self.game._sanitize_data(data[field])
                else:
                    setattr(self, field, data[field])

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


class ServerConfigGame:
    def __init__(self):
        # Define structure of the data
        self.fields = [
            "name",
            "password",
            "scenarioId",
            "mods",
        ]

        self._initiate_or_reset_data()

    def _initiate_or_reset_data(self):
        self.name = ""
        self.password = ""
        self.scenarioId = ""
        self.mods = []
        self.searchable_mods = {}

    def _sanitize_data(self, data):
        for field in self.fields:
            if field in data:
                setattr(self, field, data[field])

        self.searchable_mods = {}
        for mod in self.mods:
            mod_id = mod["modId"]
            self.searchable_mods[mod_id] = {
                "name": mod["name"],
                "version": mod["version"],
            }
