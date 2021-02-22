# -*- coding: utf-8 -*-

class Client(object):
    """A wrapper for a client."""

    def __init__(self, name, insurance="", copay=None, diagnosis=None):
        super().__init__()
        self.name = name
        self.billable_names = [name]
        self.insurance = insurance
        self.copay = copay
        self.diagnosis = diagnosis

        self.relevant_calendar_events_by_billability = {}

    def add_billable_name(self, b_name):
        self.billable_names.append(b_name)

    def add_billable_event(self, event):
        self.relevant_calendar_events_by_billability[event] = True

    def add_unbillable_event(self, event):
        self.relevant_calendar_events_by_billability[event] = False

    def change_event_billability(self, event, billability):
        self.relevant_calendar_events_by_billability[event] = billability

class ClientDirectory(object):
    """An object that stores a list of Clients."""

    def __init__(self):
        super().__init__()
        self.clients = []

    def add_client(self, name):
        client = Client(name)
        self.clients.append(client)
