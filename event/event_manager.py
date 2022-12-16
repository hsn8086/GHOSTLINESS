import logging

from .events.event_event import Event


class EventManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.synergy_events = {}

    def create_event(self, et, args, original_event=True):
        if original_event:
            self.create_event(Event, (self, et, args), original_event=False)
        else:
            if et.__name__ != 'Event':
                self.logger.debug(f'Event: {et.__name__}')
            e = et(*args)
            if et in self.synergy_events:
                for i in self.synergy_events[et]:
                    self.create_event(i, (e,))
            if not e.cancel:
                e.run()

    def reg_synergy_event(self, event):
        try:
            if event.__init__.__annotations__['e'] in self.synergy_events:
                self.synergy_events[event.__init__.__annotations__['e']].append(event)
            else:
                self.synergy_events[event.__init__.__annotations__['e']] = [event]
        except KeyError as err:
            if str(err) == "'e'":
                self.logger.exception(
                    'Please specify the parameter named "e" in the "__init__" function, and the type must be the parent event you want.')
            else:
                self.logger.exception(f'{type(err).__name__}: {str(err)}')
        except Exception as err:
            self.logger.exception(f'{type(err).__name__}: {str(err)}')
