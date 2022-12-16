import logging

from .events.event_event import Event


class EventManager:
    def __init__(self):
        self.logger=logging.getLogger(__name__)

    def create_event(self, et, args, original_event=True):
        self.logger.debug(f'Event:{str(et)}')
        if original_event:
            self.create_event(Event, (self, et, args), original_event=False)
        else:
            e = et(*args)
            if not e.cancel:
                e.run()
