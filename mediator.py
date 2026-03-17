class Mediator:
    def __init__(self):
        self._colleagues = []

    def add_colleague(self, colleague):
        self._colleagues.append(colleague)
        colleague.mediator = self

    def remove_colleague(self, colleague):
        self._colleagues.remove(colleague)
        colleague.mediator = None

    def send(self, colleague, event_d):
        for col in self._colleagues:
            if col != colleague:
                col.receive_event(event_d)


class Colleague:
    def __init__(self):
        self.mediator = None

    def send_event(self, event_d):
        self.mediator.send(self, event_d)

    def receive_event(self, event_d):
        print(f'{self.__class__.__name__} received event_d = {event_d}')
