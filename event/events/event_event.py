from ..base_event import BaseEvent


class Event(BaseEvent):
    def __init__(self, e_mgr, e, args):
        super().__init__()
        self._e_mgr = e_mgr
        self.event = e
        self.args = args

    def run(self):
        self._e_mgr.create_event(self.event, self.args,original_event=False)
