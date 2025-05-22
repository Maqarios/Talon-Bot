import time
import json

import requests

from bs4 import BeautifulSoup

import config


class WorkshopWebsiteScarper:
    def __init__(self, mod_id, dependecies={}):
        self.url = config.WORKSHOP_BASE_URL + str(mod_id)

        self.mod_id = mod_id
        self.name = None
        self.version = None

        self.dependecies = dependecies

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
        versions = json_data["props"]["pageProps"]["asset"]["versions"]
        latest_version = versions[0]
        self.name = latest_version["asset"]["name"]
        self.version = latest_version["version"]

        # Get dependencies recursively
        for dependency_id in latest_version["dependencyTree"]["dependencies"]:

            # Skip if the dependency is the same mod or already in the list
            if dependency_id == self.mod_id or dependency_id in self.dependecies:
                continue

            # Create a new instance of WorkshopWebsiteScarper for the dependency
            dependency = WorkshopWebsiteScarper(dependency_id)

            # Merge the dependency data into the current instance
            self.dependecies[dependency_id] = {
                "name": dependency.name,
                "version": dependency.version,
            }
            self.dependecies.update(dependency.dependecies)

            # Handle excessive requests
            time.sleep(1)
