import unittest
from pathlib import Path
from snakeparse.api import SnakeParseConfig, SnakeParseException

class SnakeParseConfigTest(unittest.TestCase):

    def setUp(self):
        self.snake_and_camel = [
            ('snake', 'Snake'),
            ('snake_case', 'SnakeCase'),
            ('a_b_c_d_e', 'ABCDE')
        ]

    ''' Tests for static methods '''

    def test_name_transfrom_from(self):
        self.assertIsNone(SnakeParseConfig.name_transfrom_from(key=None))

        f = SnakeParseConfig.name_transfrom_from(key='snake_to_camel')
        self.assertEqual(f('snake_case'), 'SnakeCase')

        f = SnakeParseConfig.name_transfrom_from(key='camel_to_snake')
        self.assertEqual(f('CamelCase'), 'camel_case')

        with self.assertRaises(SnakeParseException):
            SnakeParseConfig.name_transfrom_from(key='not_a_key')

    def test_snake_to_camel(self):
        f = SnakeParseConfig._snake_to_camel
        for snake, camel in self.snake_and_camel:
            self.assertEqual(f(snake), camel)
        self.assertEqual(f('snake_cAse'), 'SnakeCase')


    def test_camel_to_snake(self):
        f = SnakeParseConfig._camel_to_snake
        for snake, camel in self.snake_and_camel:
            self.assertEqual(f(camel), snake)
        self.assertEqual(f('SnakeCAse'), 'snake_c_ase')

    def test_parser_from(self):
        pass

    def test_config_parser(self):
        pass

    ''' Tests for private non-static methods '''

    ''' Tests for public methods '''

    ''' Integration tests '''
