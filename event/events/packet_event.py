import importlib
import logging

from packet.raw_packet import RawPacket
from ..base_event import BaseEvent


class PacketRecvEvent(BaseEvent):
    def __init__(self, e_mgr, conn, addr, server, raw_packet: RawPacket):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.server = server
        self.state = server.client_state_dict[addr]
        self._e_mgr = e_mgr

        try:
            # 取对应状态与包id所在的module

            packet_module = importlib.import_module(f'packet.packets.{self.state}.C0x{str(raw_packet.id)}')
            self.packet = getattr(packet_module, f'C0x{str(raw_packet.id)}')()

            # 转换包
            self.packet.from_raw_packet(raw_packet)
            logging.getLogger(__name__).debug(self.packet)

            # 取包对应事件
            event_module = importlib.import_module(f'event.events.packet_events.{self.state}.C0x{str(self.packet.packet_id)}')

            self.event = getattr(event_module,
                                 f'{self.state[0].upper() + self.state[1:]}C0x{str(self.packet.packet_id)}Event')
        except Exception as err:
            logging.getLogger(__name__).exception(type(err).__name__ + ': ' + str(err))
            self.cancel = True

    def run(self):
        # 创建事件
        self._e_mgr.create_event(self.event, (self._e_mgr, self.conn, self.server, self.packet))
