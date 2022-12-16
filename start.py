import logging

from master_server import MasterServer

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s][%(filename)s(%(lineno)d)][%(levelname)s] %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
server = MasterServer(motd='A demo of GHOSTLINESS', max_players=114514)
server.start()
