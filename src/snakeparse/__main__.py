#!/usr/bin/env python

import sys
from .api import SnakeParse
from typing import List, Optional


def main(args: Optional[List[str]]=None) -> None:
    '''The main routine.'''
    if args is None:
        args = sys.argv[1:]

    SnakeParse(args=args, config=None).run()


if __name__ == "__main__":
    main()
