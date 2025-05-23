import time
import json

import requests

from bs4 import BeautifulSoup

import config


class WorkshopWebsiteScarper:
    def __init__(self, mod_id, dependencies=None):
        self.url = config.WORKSHOP_BASE_URL + str(mod_id)

        self.mod_id = mod_id
        self.name = None
        self.version = None

        self.dependencies = {} if not dependencies else dependencies

        self.scrape()

    def scrape(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            html_data = response.text
            self.parse_data(html_data)
        else:
            print(
                f"Failed to retrieve data from {self.url}. Status code: {response.status_code}"
            )

    def parse_data(self, html_data):
        # Turn to JSON
        soup_data = BeautifulSoup(html_data, "html.parser")
        script_data = soup_data.select("script").pop(-1).get_text()
        json_data = json.loads(script_data)

        # Extract version
        asset_data = json_data["props"]["pageProps"]["asset"]
        self.name = asset_data["name"]
        self.version = asset_data["currentVersionNumber"]
        dependencies = asset_data["dependencies"]

        # Get dependencies recursively
        for dependency in dependencies:
            dependency_id = dependency["asset"]["id"]

            # Skip if the dependency is the same mod or already in the list
            if dependency_id == self.mod_id or dependency_id in self.dependencies:
                continue

            # Create a new instance of WorkshopWebsiteScarper for the dependency
            dependency_data = WorkshopWebsiteScarper(dependency_id, self.dependencies)

            # Merge the dependency data into the current instance
            self.dependencies[dependency_id] = {
                "name": dependency_data.name,
                "version": dependency_data.version,
            }
            self.dependencies.update(dependency_data.dependencies)
