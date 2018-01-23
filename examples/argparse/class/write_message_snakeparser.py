# Import the parser from snakeparse
from snakeparse.api import SnakeArgumentParser

# Implement your custom parser
class Parser(SnakeArgumentParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser.add_argument('--message', help='The message.', required=True)
