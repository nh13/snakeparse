#!/usr/bin/env python

import sys
from .api import SnakeParse, SnakeParseConfig

def main(args=None):
    '''The main routine.'''
    if args is None:
        args = sys.argv[1:]

    SnakeParse(args=args, config=None).run()

if __name__ == "__main__":
    main()
