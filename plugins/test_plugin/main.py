from event.base_event import BaseEvent
from event.events.operation_events.handshake import HandshakeEvent
from master_server import MasterServer


class E1(BaseEvent):
    def __init__(self, e: HandshakeEvent):
        super().__init__()
        self.e = e

    def run(self):
        pass


def main(server: MasterServer):
    server.event_manager.reg_synergy_event(E1)
