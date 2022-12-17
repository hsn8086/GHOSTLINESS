import logging

from master_server import MasterServer

# 程序入口
# logging配置,不像看debug可以调成logging.INFO
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(filename)s(%(lineno)d)][%(levelname)s] %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
# 创建服务器类,当然你也可以创建多个服务器类
server = MasterServer(motd='A demo of GHOSTLINESS', max_players=114514)
server.start()
