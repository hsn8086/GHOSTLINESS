import uuid
from uuid import uuid3

from packet.packets.login.S0x2 import S0x2
from ...base_event import BaseEvent


class LoginStart(BaseEvent):
    def __init__(self, conn, addr, server, name, has_uuid, uuid_):
        super().__init__()
        self.server = server
        self.conn = conn
        self.name = name
        self.addr = addr
        self.has_uuid = has_uuid
        self.uuid = uuid_

    def run(self):
        p = S0x2()
        p += self.uuid if self.has_uuid else uuid3(uuid.NAMESPACE_OID, self.name)
        p += self.name
        # p += VarInt(0)
        print(p)
        self.conn.send(bytes(p))
        self.server.client_state_dict[str(self.addr)] = 'play'
