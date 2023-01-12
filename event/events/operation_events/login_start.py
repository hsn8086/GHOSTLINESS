import uuid
from uuid import uuid3

from data_types import Array, NBT, Byte, VarInt
from packet.packets.login.S0x2 import S0x2
from packet.packets.play.S0x24 import S0x24
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
        p_s0x2 = S0x2()

        p_s0x2 += self.uuid if self.has_uuid else uuid3(uuid.NAMESPACE_OID, self.name)
        p_s0x2 += self.name
        p_s0x2 += VarInt(0)
        self.conn.send(bytes(p_s0x2))
        self.server.client_state_dict[str(self.addr)] = 'play'

        p_s0x24 = S0x24()
        p_s0x24 += 0  # player eid
        p_s0x24 += False  # is hardcore
        p_s0x24 += Byte([0])  # gamemode
        p_s0x24 += Byte([0])  # previous gamemode
        p_s0x24 += Array(seq=['minecraft:overworld'])
        nbt = NBT()
        nbt.name = 'minecraft:dimension_type'
        p_s0x24 += nbt
        # print(p_s0x24)
        # self.conn.send(bytes(p_s0x2))
