# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/04/17 10:26:47
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import pandas as pd
import typing

import utils

from storage import InfoRecDB


def dump_events(db: 'InfoRecDB'):
    def dump_timespec(db, timespec):
        def handle_rel(rel):
            if rel is None:
                return rel
            return [db.get_event(eid).title for eid in rel]
        return handle_rel(timespec.befores), handle_rel(timespec.afters), handle_rel(timespec.sames)
    event_table = []
    for eid in db.list():
        event = db.get_event(eid)
        event_table.append([str(eid), event.title, *dump_timespec(db, event.timespec)])
    return pd.DataFrame(event_table, columns=["ID", "Title", "Before", "After", "Same"])
