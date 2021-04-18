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

from exception import (
        IllegalStateError,
        )
from helper import delegate
from model import (
        AbsoluteDateTime,
        Date,
        Event,
        RelTimeMarker,
        )


DATABASE_FILE = 'db.json'

K_COLLECTION = 'collection'
K_TYPE = 'type'
K_DATA = 'data'
T_EVENT = 'event'
T_ABSOLUTEDATETIME = 'absolute_date_time'
T_DATE = 'date'
M_T_DES = {
        T_ABSOLUTEDATETIME: sede.deserialize_absolutedatetime,
        T_DATE: sede.deserialize_date,
        T_EVENT: sede.deserialise_event,
        }
M_T_SER = {
        AbsoluteDateTime: (sede.serialise_event, T_ABSOLUTEDATETIME),
        Date: (sede.serialize_date, T_DATE),
        Event: (sede.serialise_event, T_EVENT),
        }


class Collection:

    def __init__(self, initial_rel_markers: List[RelTimeMarker]=[]):
        self.collection = {}
        self._dangling_refs = {}
        for rel in initial_rel_markers:
            self.add_item(rel)

    def add_item(self, item: RelTimeMarker):
        iid = item.id
        if iid in self.collection:
            raise IllegalStateError('The item you are trying to add has duplicated id with an existing entry.')
        self.collection[iid] = item
        if isinstance(item, Event):
            if iid in self._dangling_refs:
                del self._dangling_refs[iid]
            if item.timespec:
                if item.timespec.befores is not None:
                    for tid in item.timespec.befores:
                        if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                        self._dangling_refs[tid].append(iid)
                if item.timespec.afters is not None:
                    for tid in item.timespec.afters:
                        if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                        self._dangling_refs[tid].append(iid)
                if item.timespec.sames is not None:
                    for tid in item.timespec.sames:
                        if tid not in self._dangling_refs: self._dangling_refs[tid] = []
                        self._dangling_refs[tid].append(iid)

    def is_self_contained(self) -> bool:
        '''
        Test if the collection is self-contained, which means every event points to a valid event in the collection.
        '''
        return not bool(self._dangling_refs)

    def get_item(self, id: Union[UUID, str]) -> RelTimeMarker:
        if not isinstance(id, UUID):
            id = UUID(id)
        return self.collection[id]

    def get_event(self, id: Union[UUID, str]) -> Event:
        item = self.get_item(id)
        if not isinstance(item, Event):
            raise RuntimeError("The requested item {} is not an Event, but a {}".format(id, type(item)))
        return item

    def list(self) -> Iterable[UUID]:
        return self.collection.keys()

    def has_no_conflict(self) -> bool:
        try:
            return not bool(self.conflicts())
        except nx.NetworkXUnfeasible:
            return False
        return True

    def conflicts(self):
        ordered_events = OrderedMarkers(self)
        return ordered_events.cycles()


# ForeverPast = RelTimeMarker()
# ForeverFuture = RelTimeMarker()


class OrderedMarkers:
    def __init__(self, collection: Collection):
        g = nx.DiGraph()

        def current_root(node):
            if id_merging[node] == node: return node
            return current_root(id_merging[node])
        coll = collection.collection.values()
        id_merging = {}  # k:v <==> event ID : the event ID to a parent node of its group
        for marker in coll:
            id_merging[marker.id] = marker.id
        for marker in coll:
            if isinstance(marker, Event):
                sames = marker.timespec.sames
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
                        id_merging[marker.id] = merged_id
        id_merged = {}
        for marker in coll:
            id_merged[marker.id] = current_root(marker.id)

        for marker in coll:
            if isinstance(marker, Event):
                node_id_1 = str(id_merged[marker.id])
                afters = marker.timespec.afters
                if afters:
                    for after in afters:
                        node_id_2 = str(id_merged[after])
                        g.add_edge(node_id_2, node_id_1)
                befores = marker.timespec.befores
                if befores:
                    for before in befores:
                        node_id_2 = str(id_merged[before])
                        g.add_edge(node_id_1, node_id_2)

        self.g = g

    def cycles(self):
        return list(nx.simple_cycles(self.g))



@delegate('collection', 'add_item', 'is_self_contained', 'get_event', 'get_item', 'list', 'has_no_conflict', 'conflicts')
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
            coll = []
            for entry in dic[K_COLLECTION]:
                t = entry[K_TYPE]
                assert t in M_T_DES, "DB with unexpected schema: Unknown type {} in collection".format(t)
                marker = M_T_DES[t](entry[K_DATA])
                coll.append(marker)
            return Collection(coll)

    @classmethod
    def init(cls, base_dir):
        if not cls.not_exists_or_empty_dir(base_dir):
            error(f'Path `{base_dir}` is not an empty directory or is a file')
        path = pathlib.Path(base_dir)
        if not path.exists():
            path.mkdir()
        collection = Collection()
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
        coll = []
        for marker in self.collection.collection.values():
            t = type(marker)
            assert t in M_T_SER, "Collection contains unknown type {}".format(t)
            entry = {
                    K_TYPE: M_T_SER[t][1],
                    K_DATA: M_T_SER[t][0](marker),
                    }
            coll.append(entry)
        dic[K_COLLECTION] = coll
        with open(path, 'w') as f:
            json.dump(dic, f)
