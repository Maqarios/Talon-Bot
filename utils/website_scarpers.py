import time
import json

import requests

from bs4 import BeautifulSoup

import config


def WorkshopModSearchWebsiteScarper(search_query):
    url = config.WORKSHOP_MOD_SEARCH_URL + search_query.replace(" ", "+")
    response = requests.get(url)
    if response.status_code != 200:
        print(
            f"Failed to retrieve data from {url}. Status code: {response.status_code}"
        )
        return []

    html_data = response.text
    soup_data = BeautifulSoup(html_data, "html.parser")
    script_data = soup_data.select("script").pop(-1).get_text()
    json_data = json.loads(script_data)
    asset_data = json_data["props"]["pageProps"]["assets"]
    mods = []

    for row_idx in range(min(asset_data["count"], 5)):
        row_data = asset_data["rows"][row_idx]
        mod = {}

        mod["id"] = row_data["id"]
        mod["name"] = row_data["name"]
        mod["version"] = row_data["currentVersionNumber"]

        mods.append(mod)

    return mods


class WorkshopModPageWebsiteScarper:
    def __init__(self, mod_id, dependencies=None):
        self.url = config.WORKSHOP_MOD_PAGE_URL + str(mod_id)

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
            # TODO: create a retry mechanism
            print(
                f"Failed to retrieve data from {self.url}. Status code: {response.status_code}"
            )

    def parse_data(self, html_data):
        # Turn to JSON
        soup_data = BeautifulSoup(html_data, "html.parser")
        script_data = soup_data.select("script").pop(-1).get_text()
        json_data = json.loads(script_data)

        # Extract data from JSON
        asset_data = json_data["props"]["pageProps"]["asset"]
        self.name = asset_data["name"]
        self.version = asset_data["currentVersionNumber"]
        dependencies = asset_data["dependencies"]

        # TODO: Get deep dependencies while using cache
        # Get dependencies recursively
        for dependency in dependencies:
            dependency_id = dependency["asset"]["id"]
            dependency_name = dependency["asset"]["name"]
            dependency_version = dependency["version"]

            self.dependencies[dependency_id] = {
                "name": dependency_name,
                "version": dependency_version,
            }
