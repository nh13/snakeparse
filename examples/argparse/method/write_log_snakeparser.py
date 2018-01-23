# Import the parser from snakeparse
from snakeparse.parser import argparser

def snakeparser(**kwargs):
    p = argparser(**kwargs)
    p.parser.add_argument('--message', help='The message.', required=True)
    return p
