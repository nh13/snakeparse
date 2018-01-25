import unittest
import os
from pathlib import Path
from snakeparse.api import SnakeArgumentParser, SnakeParseException
import tempfile
from .util import captured_output_streams, captured_output_to_str


class _DummySnakeArgumentParser(SnakeArgumentParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser.add_argument('--message', help='The message', required=True)


class SnakeArgumentParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = _DummySnakeArgumentParser()
        self.args_ok = ['--message', 'Hello World!']
        self.args_ok_dict = {self.args_ok[0].replace('--', '') : self.args_ok[1] }
        self.args_nok = ['--not-an-option']
        self.help_message = [
            'usage: python3.6 -m unittest [-h] --message MESSAGE', # skip this line
            '',
            'Optional options:',
            '  -h, --help         show this help message and exit',
            '  --message MESSAGE  The message'
        ]

    def test_init(self):
        self.assertIsNone(self.parser.group)
        self.assertIsNone(self.parser.description)
        self.assertIsNotNone(self.parser)

    def test_no_parsing_error(self):
        args = self.parser.parse_args(args=self.args_ok)
        self.assertDictEqual(vars(args), self.args_ok_dict)

    def test_parsing_error_raises_exception(self):
        with self.assertRaises(SnakeParseException):
            self.parser.parse_args(args=self.args_nok)

    def test_parse_args_file(self):
        filename = None
        with tempfile.NamedTemporaryFile('w', suffix='.args.txt', delete=False) as fh:
            fh.write('\n'.join(self.args_ok))
            filename = fh.name
        args = self.parser.parse_args_file(args_file=Path(filename))
        self.assertDictEqual(vars(args), self.args_ok_dict)
        os.unlink(filename)

    def test_print_help(self):
        import sys
        with captured_output_streams(as_str=False) as (stdout, stderr):
            self.parser.print_help()
        stdout = captured_output_to_str(stdout, lines=True)
        stderr = captured_output_to_str(stderr, lines=False)
        self.assertListEqual(stdout[1:], self.help_message[1:])
        self.assertEqual(stderr, '')



if __name__ == '__main__':
    unittest.main()
