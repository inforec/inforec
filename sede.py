# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/04/17 11:12:47
#   License :   Apache 2.0 (See LICENSE)
#

'''
SErialize and DEserialize
'''

from uuid import UUID

from model import (
        Event,
        RelTimeSpec,
        )


K_BEFORE = 'before'
K_AFTER = 'after'
K_SAME = 'same'
K_TIMESPEC = 'timespec'
K_ID = 'id'
K_TITLE = 'title'
K_DESC = 'desc'


def serialise_reltimespec(obj) -> dict:
    ret = {}
    if obj.befores:
        ret[K_BEFORE] = obj.befores
    if obj.afters:
        ret[K_AFTER] = obj.afters
    if obj.sames:
        ret[K_SAME] = obj.sames
    return ret

def deserialise_reltimespec(dic) -> 'RelTimeSpec':
    befores = dic.get(K_BEFORE, None)
    afters = dic.get(K_AFTER, None)
    sames = dic.get(K_SAME, None)
    return RelTimeSpec(befores=befores, afters=afters, sames=sames)
    # if before is not None or after is not None:
    #     assert K_SAME not in dic
    #     return RelTimeSpec(before=before, after=after)
    # else:
    #     return RelTimeSpec(same=same)


def deserialise_event(dic) -> 'Event':
    id = UUID(dic[K_ID])
    title = dic[K_TITLE]
    desc = dic.get(K_DESC, None)
    timespec_se = dic.get(K_TIMESPEC, None)
    timespec = deserialise_reltimespec(timespec_se) if timespec_se else None
    return Event(id=id, title=title, desc=desc, timespec=timespec)

def serialise_event(obj) -> dict:
    ret = {
            K_ID: str(obj.id),
            K_TITLE: obj.title,
            }
    if obj.desc:
        ret[K_DESC] = obj.desc
    if obj.timespec:
        ret[K_TIMESPEC] = serialise_reltimespec(obj.timespec)
    return ret
