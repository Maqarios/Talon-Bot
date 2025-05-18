import time

import config
from cogs.mos import MosCog
from cogs.serverconfig import ServerConfigCog
from utils.utils import add_player_to_playersgroups
from utils.file_watchers import ServerConfigFileWatcher
from utils.cache import ActivePlayersBohemiaIDCache
from cogs.user import UserCog

# server_config = ServerConfigFileWatcher(config.SERVERCONFIG_PATH)
# server_config.start()

# while True:
#     time.sleep(1)

add_player_to_playersgroups(config.PLAYERSGROUPS_PATH, "certifiedGMs", "TEST")
