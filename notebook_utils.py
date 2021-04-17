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


def dump_events(info_rec_db: 'InfoRecDB'):
    event_table = utils.tabularize_events(info_rec_db)
    return pd.DataFrame(event_table, columns=["ID", "Title"])
