# Import the parser from snakeparse
from snakeparse.parser import argparser

def snakeparser(**kwargs):
    p = argparser(**kwargs)
    p.parser.add_argument('--message', help='The message.', required=True)
    return p

# Get the arguments from the config file; this should always succeed.
args = snakeparser().parse_config(config=config)

rule all:
    input:
        'log.txt'

# A simple rule to write the message to the output
rule message:
    output: 'log.txt'
    shell: 'echo {args.message} > {output}'
