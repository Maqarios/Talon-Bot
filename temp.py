import time

import config
from cogs.mos import MosCog
from cogs.serverconfig import ServerConfigCog
from utils.file_watchers import ServerConfigFileWatcher
from utils.cache import ActivePlayersBohemiaIDCache

server_config = ServerConfigFileWatcher(config.SERVERCONFIG_PATH)
server_config.start()

# while True:
#     time.sleep(1)
