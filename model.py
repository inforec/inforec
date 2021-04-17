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

from typing import Iterable, List, Mapping, Optional, Union
from uuid import (
        uuid4 as genid,
        UUID,
        )


class RelTimeMarker:
    '''
    A class representing a relative time, which may be relative to another event or absolute to clock.
    Maybe using subclasses is neater.
    '''
    pass


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


class Event(RelTimeMarker):

    @classmethod
    def between(cls, before, after, title, desc=None):
        id = uuid.uuid4()
        ts = RelTimeSpec(before=before, after=after)
        return cls(id=id, title=title, desc=desc, timespec=ts)

    @classmethod
    def before(cls, before, title, desc=None):
        id = uuid.uuid4()
        ts = RelTimeSpec(before=before)
        return cls(id=id, title=title, desc=desc, timespec=ts)

    @classmethod
    def after(cls, after, title, desc=None):
        id = uuid.uuid4()
        ts = RelTimeSpec(after=after)
        return cls(id=id, title=title, desc=desc, timespec=ts)

    @classmethod
    def same(cls, same, title, desc=None):
        id = uuid.uuid4()
        ts = RelTimeSpec(same=same)
        return cls(id=id, title=title, desc=desc, timespec=ts)

    @classmethod
    def single(cls, title, desc=None):
        id = uuid.uuid4()
        return cls(id=id, title=title, desc=desc)


    def __init__(self, id, title, desc=None, timespec=None):
        self.id = id
        self.title = title
        self.desc = desc
        self.timespec = timespec
