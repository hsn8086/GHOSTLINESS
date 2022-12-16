from .event import Event


class EventManager:
    def __init__(self):
        pass

    def create_event(self, e, args, original_event=True):
        if original_event:
            self.create_event(Event, (self, e, args), original_event=False)
        else:
            if e(self, e, *args):
                e.run()
