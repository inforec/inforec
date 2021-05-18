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

import datetime

from uuid import UUID

from model import (
        AbsoluteDateTime,
        Date,
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
K_DATETIME = 'datetime'
K_DATE = 'date'


DATETIME_REPR = r'%Y-%m-%dT%H:%M:%S[%Z]'
DATE_REPR = r'%Y-%m-%d[%Z]'


def serialise_reltimespec(obj) -> dict:
    ret = {}
    if obj.befores:
        ret[K_BEFORE] = [str(item) for item in obj.befores]
    if obj.afters:
        ret[K_AFTER] = [str(item) for item in obj.afters]
    if obj.sames:
        ret[K_SAME] = [str(item) for item in obj.sames]
    return ret

def deserialise_reltimespec(dic) -> RelTimeSpec:
    if dic is None:  # Compatibility. Will be removed
        return RelTimeSpec()
    def uuidfy(items):
        return [UUID(item) for item in items] if items is not None else None
    befores = uuidfy(dic.get(K_BEFORE, None))
    afters = uuidfy(dic.get(K_AFTER, None))
    sames = uuidfy(dic.get(K_SAME, None))
    return RelTimeSpec(befores=befores, afters=afters, sames=sames)
    # if before is not None or after is not None:
    #     assert K_SAME not in dic
    #     return RelTimeSpec(before=before, after=after)
    # else:
    #     return RelTimeSpec(same=same)


def deserialise_event(dic) -> Event:
    id = UUID(dic[K_ID])
    title = dic[K_TITLE]
    desc = dic.get(K_DESC, None)
    timespec_se = dic.get(K_TIMESPEC, None)
    timespec = deserialise_reltimespec(timespec_se)
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


def deserialize_absolutedatetime(dic) -> AbsoluteDateTime:
    id = UUID(dic[K_ID])
    time = datetime.strptime(dic[K_DATETIME], DATETIME_REPR)
    return AbsoluteDateTime(id, time)

def serialize_absolutedatetime(obj: AbsoluteDateTime) -> dict:
    ret = {
            K_ID: str(obj.id),
            K_DATETIME: obj.abstime.strftime(DATETIME_REPR),
            }
    return ret


def deserialize_date(dic) -> Date:
    id = UUID(dic[K_ID])
    time = datetime.datetime.strptime(dic[K_DATE], DATE_REPR)
    return Date(id, time)

def serialize_date(obj: Date) -> dict:
    ret = {
            K_ID: str(obj.id),
            K_DATE: obj.date.strftime(DATE_REPR),
            }
    return ret
