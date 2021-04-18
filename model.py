# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/04/17 11:10:27
#   License :   Apache 2.0 (See LICENSE)
#

'''
This file contains the data model.
'''

import datetime

from enum import Enum
from exception import (
        IllegalStateError,
        )
from typing import Iterable, List, Mapping, Optional, Union
from uuid import (
        uuid4 as genid,
        UUID,
        )


class TimeRelativity(Enum):
    BEFORE = 1  # If the RelTimeMarker is strictly before the other.
    SAME = 10  # If the RelTimeMarker is the same as the other. This is a rare case, and will only happen with asserted sames and absolute time. Most often a PARALLEL is expected.
    PARALLEL = 11  # If the order can't be determined. Can be considered as unknown.
    AFTER = 20  # If the RelTimeMarker is strictly after the other.


class RelTimeMarker:
    '''
    A class representing a relative time, which may be relative to another event or absolute to clock.
    Maybe using subclasses is neater.
    '''
    def __init__(self, id):
        self.id = id


class RelTimeSpec:
    '''
    A class representing a specification of relative time, which should be before, after, or is at the same time as some `RelTimeMarker`.
    '''

    def __init__(self, befores: Optional[List[UUID]]=None, afters: Optional[List[UUID]]=None, sames: Optional[List[UUID]]=None):
        '''
        None means this field is unknown, while an empty list means this field is known to be empty
        '''
        # assert bool(before or after) != bool(absolute), 'An event should not be either relative or absolute. Maybe you want to add the relative information to the other events.'
        self.befores = befores
        self.afters = afters
        self.sames = sames

    def before(self, other: RelTimeMarker):
        self.befores.append(other)

    def after(self, other: RelTimeMarker):
        self.afters.append(other)

    def same(self, other: RelTimeMarker):
        self.sames.append(other)


class AbsoluteDateTime(RelTimeMarker):

    def __init__(self, id, abstime: datetime.datetime):
        super().__init__(id)
        self.abstime = time

    def compare(self, o: 'RelTimeMarker') -> TimeRelativity:
        if isinstance(o, AbsoluteDateTime):
            if self.abstime < o.abstime:
                return TimeRelativity.BEFORE
            elif self.abstime == o.abstime:
                return TimeRelativity.SAME
            elif self.abstime > o.abstime:
                return TimeRelativity.AFTER
            else:
                raise IllegalStateError('AbsoluteDateTime comparison exausted but not found')
        return NotImplemented


class Date(RelTimeMarker):

    def __init__(self, id, date: datetime.date):
        super().__init__(id)
        self.date = date


class Event(RelTimeMarker):

    def __init__(self, id, title, timespec, desc=None):
        super().__init__(id)
        self.title = title
        self.desc = desc
        self.timespec = timespec


class EventBuilder:
    def __init__(self, title):
        self._title = title
        self._id = None
        self._desc = None
        self._before = None
        self._after = None
        self._same = None

    def id(self, id):
        self._id = id
        return self

    def desc(self, desc):
        self._desc = desc
        return self

    def _add_rel(self, spec_target, other):
        if isinstance(other, Event):
            spec_target.append(other.id)
        elif isinstance(other, UUID):
            spec_target.append(other)
        else:
            spec_target.append(UUID(other))

    def before(self, other):
        if self._before is None:
            self._before = []
        self._add_rel(self._before, other)
        return self

    def after(self, other):
        if self._after is None:
            self._after = []
        self._add_rel(self._after, other)
        return self

    def same(self, other):
        if self._same is None:
            self._same = []
        self._add_rel(self._same, other)
        return self

    def build(self) -> Event:
        before = []
        timespec = RelTimeSpec(self._before, self._after, self._same)
        eid = self._id if self._id else genid()
        return Event(id=eid, title=self._title, desc=self._desc, timespec=timespec)

