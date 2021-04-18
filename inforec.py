#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/03/01 17:47:31
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import argparse
import sys

from model import EventBuilder
from storage import InfoRecDB
from utils import tabularize_events


DEFAULT_DIR = '.'


def error(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='action',
            dest='action',
            help='The action to perform')

    parser.add_argument('-d', '--directory', nargs='?', default=DEFAULT_DIR)

    subparser = subparsers.add_parser('init')

    subparser = subparsers.add_parser('list')

    subparser = subparsers.add_parser('add')
    subparser.add_argument('title')
    subparser.add_argument('desc', nargs='?', default=None)
    subparser.add_argument('--before', nargs='?', default=None)
    subparser.add_argument('--after', nargs='?', default=None)
    subparser.add_argument('--same', nargs='?', default=None)

    args = parser.parse_args()

    base_dir = args.directory
    if args.action == 'init':
        InfoRecDB.init(base_dir)
    elif args.action == 'list':
        db = InfoRecDB.open(base_dir)
        for einfo in tabularize_events(db):
            print(f"{einfo[0]} {einfo[1]}")
    elif args.action == 'add':
        title = args.title
        desc = args.desc
        before = args.before
        after = args.after
        same = args.same
        db = InfoRecDB.open(base_dir)
        event = EventBuilder(title).desc(desc).before(before).after(after).same(same).build()
        db.add_event(event)
        assert db.is_self_contained()
        db.write()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

