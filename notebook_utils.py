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

from exception import IllegalStateError
from model import Event
from storage import InfoRecDB


def dump_events(db: 'InfoRecDB'):
    def dump_timespec(db, timespec):
        def handle_rel(rel):
            if rel is None:
                return rel
            return [str(db.get_item(iid)) for iid in rel]
        return handle_rel(timespec.befores), handle_rel(timespec.afters), handle_rel(timespec.sames)
    event_table = []
    for iid in db.list():
        item = db.get_item(iid)
        if isinstance(item, Event):
            event_table.append([str(iid), item.title, *dump_timespec(db, item.timespec)])
    return pd.DataFrame(event_table, columns=["ID", "Title", "Before", "After", "Same"])
