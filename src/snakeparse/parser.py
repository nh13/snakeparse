'''Convenience methods for creating SnakeMake command line parsers.

The module contains the following public methods:

    - argparse(**kwargs) -- A method to create an initialized argparse parser.
        Used in the snakeparser method defined in your snakeparse file when
        implementing parsing with the argparse module.
'''
from .api import SnakeArgumentParser


def argparser(**kwargs):
    ''' Returns an SnakeParser that has an initialized member variable parser
    of type argparse.ArgumentParser.  The keyword arguments are passed to the
    constructor of argparse.ArgumentParser.
    '''
    class Parser(SnakeArgumentParser):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    return Parser(**kwargs)
