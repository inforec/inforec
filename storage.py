# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/04/17 10:46:34
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains all that is related to storage and backend data structures.
It may be split in the future.
'''

import json
import networkx
import pathlib
import uuid

from typing import Iterable, List, Mapping, Optional, Union
from uuid import UUID

from helper import delegate


DATABASE_FILE = 'db.json'


K_EVENTS = 'events'
K_BEFORE = 'before'
K_AFTER = 'after'
K_SAME = 'same'
K_TIMESPEC = 'timespec'
K_ID = 'id'
K_TITLE = 'title'
K_DESC = 'desc'


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
    @staticmethod
    def serialise(obj) -> dict:
        ret = {}
        if obj.before:
            ret[K_BEFORE] = obj.before
        if obj.after:
            ret[K_AFTER] = obj.after
        if obj.same:
            ret[K_SAME] = obj.same
        return ret

    @staticmethod
    def deserialise(dic) -> 'RelTimeSpec':
        before = dic.get(K_BEFORE, None)
        after = dic.get(K_AFTER, None)
        same = dic.get(K_SAME, None)
        return RelTimeSpec(before=before, after=after, same=same)
        # if before is not None or after is not None:
        #     assert K_SAME not in dic
        #     return RelTimeSpec(before=before, after=after)
        # else:
        #     return RelTimeSpec(same=same)


    def __init__(self, before: Optional[List[RelTimeMarker]]=None, after: Optional[List[RelTimeMarker]]=None, same: Optional[List[RelTimeMarker]]=None):
        '''
        None means this field is unknown, while an empty list means this field is known to be empty
        '''
        # assert bool(before or after) != bool(absolute), 'An event should not be either relative or absolute. Maybe you want to add the relative information to the other events.'
        self.before = before
        self.after = after
        self.same = same


class Event(RelTimeMarker):

    @staticmethod
    def deserialise(dic) -> 'Event':
        id = UUID(dic[K_ID])
        title = dic[K_TITLE]
        desc = dic.get(K_DESC, None)
        timespec_se = dic.get(K_TIMESPEC, None)
        timespec = RelTimeSpec.deserialise(timespec_se) if timespec_se else None
        return Event(id=id, title=title, desc=desc, timespec=timespec)

    @staticmethod
    def serialise(obj) -> dict:
        ret = {
                K_ID: str(obj.id),
                K_TITLE: obj.title,
                }
        if obj.desc:
            ret[K_DESC] = obj.desc
        if obj.timespec:
            ret[K_TIMESPEC] = obj.timespec
        return ret


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


class EventCollection:

    def __init__(self, initial_events: List[Event]=[]):
        self.events = {}
        self._dangling_refs = {}
        for event in initial_events:
            self.add_event(event)

    def add_event(self, event: Event):
        eid = event.id
        if eid in self.events:
            raise RuntimeError('The event you are trying to add has duplicated id with an existing entry.')
        self.events[eid] = event
        if eid in self._dangling_refs:
            del self._dangling_refs[eid]
        if event.timespec:
            if event.timespec.before is not None:
                for tid in event.timespec.before:
                    if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                    self._dangling_refs[tid].append(eid)
            if event.timespec.after is not None:
                for tid in event.timespec.after:
                    if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                    self._dangling_refs[tid].append(eid)
            if event.timespec.same is not None:
                tid = event.timespec.same.id
                if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                self._dangling_refs[tid].append(eid)

    def is_self_contained(self) -> bool:
        '''
        Test if the collection is self-contained, which means every event points to a valid event in the collection.
        '''
        return not bool(self._dangling_refs)

    def get_event(self, id: Union[UUID, str]) -> Event:
        if not isinstance(id, UUID):
            id = UUID(id)
        return self.events[id]

    def list(self) -> Iterable[UUID]:
        return self.events.keys()

    def has_no_conflict(self) -> bool:
        try:
            ordered_events = OrderedEvents(self.events.values())
        except networkx.NetworkXUnfeasible:
            return False
        return True


ForeverPast = RelTimeMarker()
ForeverFuture = RelTimeMarker()


class OrderedEvents:
    def __init__(self, events: Iterable[Event]):
        g = networkx.DiGraph()

        def current_root(node):
            if id_merging[node] == node: return node
            return current_root(id_merging[node])
        id_merging = {}  # k:v <==> event ID : the event ID to a parent node of its group
        for event in events:
            id_merging[event.id] = event.id
        for event in events:
            if event.timespec:
                sames = event.timespec.same
                if sames:
                    merged_id = None
                    for same in sames:
                        if id_merging[same] != same:
                            merged_id = id_merging[same]
                            break
                    if merged_id:
                        for same in sames:
                            root = current_root(same)
                            id_merging[same] = merged_id
                        id_merging[event.id] = merged_id
        id_merged = {}
        for event in events:
            id_merged[event.id] = current_root(event.id)

        for event in events:
            if event.timespec:
                node_id_1 = str(id_merged[event.id])
                afters = event.timespec.after
                if afters:
                    for after in afters:
                        node_id_2 = str(id_merged[after])
                        g.add_edge(node_id_2, node_id_1)
                befores = event.timespec.before
                if befores:
                    for before in befores:
                        node_id_2 = str(id_merged[before])
                        g.add_edge(node_id_1, node_id_2)

        self.g = g


@delegate('collection', 'add_event', 'is_self_contained', 'get_event', 'list', 'has_no_conflict')
class InfoRecDB:

    @staticmethod
    def not_exists_or_empty_dir(dir_path):
        path = pathlib.Path(dir_path)
        if not path.exists(): return True
        if not path.is_dir(): return False
        subs = list(path.glob('*'))
        return not bool(subs)

    @staticmethod
    def read_db(directory):
        path = pathlib.Path(directory) / DATABASE_FILE
        with open(path, 'r') as f:
            dic = json.load(f)
            events = []
            for entry in dic[K_EVENTS]:
                event = Event.deserialise(entry)
                events.append(event)
            return EventCollection(events)

    @classmethod
    def init(cls, base_dir):
        if not cls.not_exists_or_empty_dir(base_dir):
            error(f'Path `{base_dir}` is not an empty directory or is a file')
        path = pathlib.Path(base_dir)
        if not path.exists():
            path.mkdir()
        collection = EventCollection()
        db = cls(base_dir, collection)
        db.write()

    @classmethod
    def open(cls, base_dir):
        collection = cls.read_db(base_dir)
        return cls(base_dir, collection)

    def __init__(self, directory, collection):
        self._dir = directory
        self.collection = collection

    def write(self):
        path = pathlib.Path(self._dir) / DATABASE_FILE
        dic = {}
        dic[K_EVENTS] = [Event.serialise(event) for event in self.collection.events.values()]
        with open(path, 'w') as f:
            json.dump(dic, f)
