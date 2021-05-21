# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/04/17 10:32:46
#   License :   Apache 2.0 (See LICENSE)
#

'''
General utils. They may be used in `notebook_utils` as well.
'''

import typing

from storage import InfoRecDB


def tabularize_events(db: 'InfoRecDB'):
    event_table = []
    for eid in db.list():
        event = db.get_event(eid)
        event_table.append([str(eid), event.title])
    return event_table

def comma_separated_list(lst_s):
    return [item.strip() for item in lst_s.split(',')]
