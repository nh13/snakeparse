# Import the parser from snakeparse
from snakeparse.api import SnakeArgumentParser

# Implement your custom parser
class Parser(SnakeArgumentParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser.add_argument('--message', help='The message.', required=True)

# Get the arguments from the config file; this should always succeed.
args = Parser().parse_config(config=config)

rule all:
    input:
        'log.txt'

# A simple rule to write the message to the output
rule message:
    output: 'log.txt'
    shell: 'echo {args.message} > {output}'
