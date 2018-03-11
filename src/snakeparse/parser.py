'''Convenience methods for creating SnakeMake command line parsers.

The module contains the following public methods:

    - :func:`~snakeparse.parser.argparse` -- A method to create an initialized
      argparse parser (:class:`~snakeparse.api.SnakeArgumentParser`). Use in the
      snakeparser method defined in your snakeparse  file when implementing
      parsing with the :module:`~argparse` module.
'''
from .api import SnakeArgumentParser


def argparser(**kwargs) -> SnakeArgumentParser:
    ''' Returns an SnakeParser that has an initialized member variable parser
    of type :class:`~argparse.ArgumentParser`.  The keyword arguments are passed to the
    constructor of :class:`~argparse.ArgumentParser`.
    '''
    class Parser(SnakeArgumentParser):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    return Parser(**kwargs)
