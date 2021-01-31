# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

class DateRange(object):
    """docstring for DateRange."""

    def __init__(self, start, end):
        super(DateRange, self).__init__()
        assert type(start) == datetime
        assert type(end) == datetime
        self.start = start
        self.end = end

        self.events = []

    def set_start(self, new_start):
        self.start = new_start

    def set_end(self, new_end):
        self.end = new_end

    def add_events(self, new_events):
        self.events.extend(new_events)

    def get_events(self):
        return self.events

    def get_last_event(self):
        if not self.events:
            return None
        return self.events[-1]

    def __repr__(self):
        return "({}, {})".format(self.start.strftime("%m/%d/%Y"), self.end.strftime("%m/%d/%Y"))

class CalendarManager(object):
    """docstring for CalendarManager."""

    TIME_DELTA = 7

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.date_ranges = []

    def icloud(self):
        return self.parent.icloud

    def download_date_range(self, date_range):
        cal = self.icloud().calendar
        cal.refresh_client(from_dt=date_range.start,to_dt=date_range.end)

        return [CalendarEvent(event) for event in cal.response['Event']]

    def add_one_day(self, date):
        # Pre-download TIME_DELTA days in advance
        date_and_extra = DateRange(date, date + timedelta(days=self.TIME_DELTA))
        return self.add_date_range(date_and_extra)

    def add_date_range(self, date_range):
        """A function that will perform the actions needed
           in order to add the specified DateRange to the
           manager's date_ranges list. Then returns whichever
           DateRange object contains all the event information
           that happens within date_range.

           NOTE: This should end up with all the date_ranges sorted
           by date, but it doesn't. I think it's something about synchronicity.
           Maybe downloads take some time? If I fix this, the searches become faster.
           TODO: Fix the timing of the downloads. (And change searches to sorted)
           """

        # Define the logic that will allow for the merging and deletion
        # of date ranges in order tp consolidate everything
        dr_focus = date_range
        dr_focus_date = date_range.start
        added_dr = False
        added_anything = False
        dr_to_delete = []
        for index, old_dr in enumerate(self.date_ranges):
            if old_dr.end < dr_focus.start:
                # The older date_range is irrelevant
                continue
            else:
                added_anything = True
            if old_dr.start > dr_focus.end:
                break
            if dr_focus == date_range and not added_dr and dr_focus.start < old_dr.start:
                # Add the date_range if it starts it's own range and doesn't exist
                index_to_insert_at = index
                added_dr = True
            if dr_focus == date_range and date_range.start >= old_dr.start and date_range.start <= old_dr.end:
                # If the date_range starts in the middle of an older date_range,
                # the old dr becomes the focus.
                dr_focus = old_dr
                dr_focus_date = dr_focus.end
                self.extend_dr_forwards(dr_focus, date_range.end)
                continue
            if dr_focus_date < old_dr.start:
                # Download from the dr_focus_date to the start of a downloaded segment
                download_segment = DateRange(dr_focus_date, old_dr.start)
                self.download_to_dr(dr_focus, download_segment)

                dr_focus_date = old_dr.end
            if old_dr.start >= dr_focus.start and old_dr.end <= dr_focus.end:
                # The older date range is contained completely within
                # either the new date_range or the extended date range
                # (The value of dr_focus)
                self.merge_dr(old_dr, dr_focus)
                dr_to_delete.append(old_dr)
            if old_dr.start <= dr_focus.end and old_dr.start >= dr_focus.start and old_dr.end >= dr_focus.end:
                # The older date range lies on the boundary pf the dr in focus.
                # The older dtae range should be deleted, and dr_focus extended
                self.extend_dr_forwards(dr_focus, old_dr.end)
                self.merge_dr(old_dr, dr_focus)
                dr_to_delete.append(old_dr)
                dr_focus_date = old_dr.end

        # If the list is empty, or date_range goes at the end,
        # just make this new one.
        if len(self.date_ranges) == 0 or not added_anything:
            self.date_ranges.append(date_range)
            self.download_to_dr(date_range, date_range)
            return date_range

        # Download the extra bit between the end of the last old dr and date_range
        if dr_focus_date != dr_focus.end:
            download_segment = DateRange(dr_focus_date, dr_focus.end)
            self.download_to_dr(dr_focus, download_segment)

        if added_dr:
            self.date_ranges.insert(index_to_insert_at, date_range)

        for dr in dr_to_delete:
            self.date_ranges.remove(dr)
            del dr

        return dr_focus

    def merge_dr(self, dr_delete, dr_merge):
        # merge the data from dr_delete to dr_merge
        dr_merge.add_events(dr_delete.get_events())

    def extend_dr_forwards(self, dr_extend, new_end):
        assert new_end >= dr_extend.end
        dr_extend.set_end(new_end)

    def extend_dr_backwards(self, dr_extend, new_start):
        assert new_start <= dr_extend.start
        dr_extend.set_start(new_start)

    def download_to_dr(self, relevant_dr, download_dr):
        events = self.download_date_range(download_dr)

        # Ensure the new events are being added to the right place
        last_old_event = relevant_dr.get_last_event()
        first_new_event = events[0]

        assert not last_old_event or (first_new_event.date >= last_old_event.date)

        relevant_dr.add_events(events)

    def __repr__(self):
        readable = "["
        for dr in self.date_ranges:
            readable += "{}, ".format(repr(dr))
        readable += "]"
        return readable

class CalendarEvent(object):
    """docstring for CalendarEvent."""

    def __init__(self, calendar_dict):
        super(CalendarEvent, self).__init__()
        self.title = calendar_dict.get("title")

        self.date = calendar_dict["localStartDate"]
        self.date = datetime(self.date[1], self.date[2], self.date[3])

        self.duration_in_min = int(calendar_dict["duration"])

    def readable_date(self):
        return self.date.strftime("%m/%d/%Y")
