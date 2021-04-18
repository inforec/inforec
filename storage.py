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
import networkx as nx
import pathlib
import uuid

from typing import Iterable, List, Mapping, Optional, Union
from uuid import UUID

import sede

from helper import delegate
from model import (
        Event,
        RelTimeMarker,
        )


DATABASE_FILE = 'db.json'

K_EVENTS = 'events'


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
            if event.timespec.befores is not None:
                for tid in event.timespec.befores:
                    if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                    self._dangling_refs[tid].append(eid)
            if event.timespec.afters is not None:
                for tid in event.timespec.afters:
                    if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                    self._dangling_refs[tid].append(eid)
            if event.timespec.sames is not None:
                for tid in event.timespec.sames:
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
            return not bool(self.conflicts())
        except nx.NetworkXUnfeasible:
            return False
        return True

    def conflicts(self):
        ordered_events = OrderedEvents(self)
        return ordered_events.cycles()


ForeverPast = RelTimeMarker()
ForeverFuture = RelTimeMarker()


class OrderedEvents:
    def __init__(self, collection: EventCollection):
        g = nx.DiGraph()

        def current_root(node):
            if id_merging[node] == node: return node
            return current_root(id_merging[node])
        events = collection.events.values()
        id_merging = {}  # k:v <==> event ID : the event ID to a parent node of its group
        for event in events:
            id_merging[event.id] = event.id
        for event in events:
            if event.timespec:
                sames = event.timespec.sames
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
                afters = event.timespec.afters
                if afters:
                    for after in afters:
                        node_id_2 = str(id_merged[after])
                        g.add_edge(node_id_2, node_id_1)
                befores = event.timespec.befores
                if befores:
                    for before in befores:
                        node_id_2 = str(id_merged[before])
                        g.add_edge(node_id_1, node_id_2)

        self.g = g

    def cycles(self):
        return list(nx.simple_cycles(self.g))



@delegate('collection', 'add_event', 'is_self_contained', 'get_event', 'list', 'has_no_conflict', 'conflicts')
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
                event = sede.deserialise_event(entry)
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
        dic[K_EVENTS] = [sede.serialise_event(event) for event in self.collection.events.values()]
        with open(path, 'w') as f:
            json.dump(dic, f)
