import unittest
from pathlib import Path
from snakeparse.api import _ArgumentParser, SnakeParseException

class ArgumentParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = _ArgumentParser()
        self.parser.add_argument('--message', help='The message', required=True)
        self.args_ok  = ['--message', 'Hello World!']
        self.args_nok = ['--not-an-option']

    def test_no_parsing_error(self):
        args = self.parser.parse_args(args=self.args_ok)
        self.assertDictEqual(vars(args), {self.args_ok[0].replace('--', '') : self.args_ok[1] })

    def test_parsing_error_raises_exception(self):
        with self.assertRaises(SnakeParseException):
            self.parser.parse_args(args=self.args_nok)

if __name__ == '__main__':
    unittest.main()
