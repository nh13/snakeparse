import unittest
from pathlib import Path
import tempfile
from snakeparse.api import SnakeParseConfig, SnakeParseException, SnakeParseWorkflow

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
        self.assertEqual(f(''), '')

    def _get_snakefile_and_workflow(self, snakefile_contents):
        with tempfile.NamedTemporaryFile('w', suffix='.smk', delete=False) as fh:
            fh.write(snakefile_contents)
            snakefile = Path(fh.name)
        workflow = SnakeParseWorkflow(name='Workflow', snakefile=snakefile, group=None, description=None)
        return (snakefile, workflow)

    def _test_parser_from_helper(self, snakefile_contents):
        snakefile, workflow = self._get_snakefile_and_workflow(snakefile_contents=snakefile_contents)
        parser = SnakeParseConfig.parser_from(workflow=workflow)
        args   = parser.parse_args(['--message', 'Hello World!'])
        self.assertEqual(args.message, 'Hello World!')
        with self.assertRaises(SnakeParseException):
            args = parser.parse_args(['--not-an-arg', 'Hello World!'])
        snakefile.unlink()

    def test_parser_from_method(self):
        ''' Tests a snakeparser method in the snakefile '''
        snakefile_contents = '''
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
        '''
        self._test_parser_from_helper(snakefile_contents=snakefile_contents)

    def test_config_parser_from_class(self):
        ''' Tests a SnakeArgumentParser class in the snakefile '''
        snakefile_contents = '''
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
        '''
        self._test_parser_from_helper(snakefile_contents=snakefile_contents)

    def test_config_parser_no_methods_or_classes(self):
        ''' Tests a failure when we have no parser in the snakefile '''
        snakefile, workflow = self._get_snakefile_and_workflow(snakefile_contents='')
        with self.assertRaises(SnakeParseException) as ex:
            SnakeParseConfig.parser_from(workflow=workflow)
        self.assertIn('Could not find either', str(ex.exception))

    def test_config_parser_both_method_and_classes(self):
        ''' Tests a failure when we have multiple parsers in the snakefile '''
        imports = '''
from snakeparse.parser import argparser
from snakeparse.api import SnakeArgumentParser
        '''

        class_parser_foo = '''
class ParserFoo(SnakeArgumentParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser.add_argument('--message', help='The message.', required=True)
        '''

        class_parser_bar = '''
class ParserBar(SnakeArgumentParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser.add_argument('--message', help='The message.', required=True)
        '''

        method_snakeparser = '''
def snakeparser(**kwargs):
    p = argparser(**kwargs)
    p.parser.add_argument('--message', help='The message.', required=True)
    return p
        '''

        rules = '''
rule all:
    input:
        'log.txt'

# A simple rule to write the message to the output
rule message:
    output: 'log.txt'
    shell: 'echo {args.message} > {output}'
        '''

        snakefile_contents_a = imports + \
            class_parser_foo + \
            class_parser_bar + \
            '\nargs = ParserFoo().parse_config(config=config)\n' + \
            rules

        snakefile_contents_b = imports + \
            class_parser_foo + \
            method_snakeparser + \
            '\nargs = snakeparser().parse_config(config=config)\n' + \
            rules

        snakefile_contents_c = imports + \
            class_parser_foo + \
            class_parser_bar + \
            method_snakeparser + \
            '\nargs = snakeparser().parse_config(config=config)\n' + \
            rules
        for snakefile_contents in [snakefile_contents_a, snakefile_contents_b, snakefile_contents_c]:
            snakefile, workflow = self._get_snakefile_and_workflow(snakefile_contents=snakefile_contents)
            with self.assertRaises(SnakeParseException) as ex:
                SnakeParseConfig.parser_from(workflow=workflow)
            self.assertIn('Found', str(ex.exception))

    def test_config_parser(self):
        parser = SnakeParseConfig.config_parser()

        # test that it doesn't exit, but instead raises an error
        with self.assertRaises(SnakeParseException):
            parser.parse_args(['-h'])
        with self.assertRaises(SnakeParseException):
            parser.parse_args(['--help'])
        with self.assertRaises(SnakeParseException) as ctx:
            parser.parse_args(['--not-an-arg'])
        self.assertIn('unrecognized arguments', str(ctx.exception))

        # should require no arguments
        args = parser.parse_args(args=[])
        self.assertIsNone(args.config)

    def test_add_workflow(self):
        with tempfile.NamedTemporaryFile('w', suffix='.smk', delete=False) as fh:
            fh.write('')
            snakefile = Path(fh.name)
        wf1 = SnakeParseWorkflow(name='N1', snakefile=snakefile)
        wf2 = SnakeParseWorkflow(name='N2', snakefile=snakefile)
        # test adding more than one workflows
        config = SnakeParseConfig()
        config.add_workflow(workflow=wf1)
        config.add_workflow(workflow=wf2)
        self.assertEqual(len(config.workflows), 2)
        # test failure with a workflow with the same name
        with self.assertRaises(SnakeParseException):
            config.add_workflow(workflow=wf1)
        self.assertEqual(len(config.workflows), 2)

    def test_add_snakefile(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)
            # test adding more than one snakefile
            self.assertTrue(tempdir.exists())
            snakefile_a = tempdir / 'workflow_a.smk'
            snakefile_b = tempdir / 'WorkflowB.smk'

            with snakefile_a.open('w') as fh:
                fh.write('')
            with snakefile_b.open('w') as fh:
                fh.write('')

            # test failure with a snakefile with the same name
            config = SnakeParseConfig()
            config.add_snakefile(snakefile=snakefile_a)
            config.add_snakefile(snakefile=snakefile_b)
            self.assertEqual(len(config.workflows), 2)
            with self.assertRaises(SnakeParseException):
                config.add_snakefile(snakefile=snakefile_a)

            # test when name transform is set
            config = SnakeParseConfig(name_transform=SnakeParseConfig.name_transfrom_from('snake_to_camel'))
            config.add_snakefile(snakefile=snakefile_a)
            config.add_snakefile(snakefile=snakefile_b)
            self.assertListEqual([wf.name for wf in config.workflows.values()], ['WorkflowA', 'Workflowb'])

            config = SnakeParseConfig(name_transform=SnakeParseConfig.name_transfrom_from('camel_to_snake'))
            config.add_snakefile(snakefile=snakefile_a)
            config.add_snakefile(snakefile=snakefile_b)
            self.assertListEqual([wf.name for wf in config.workflows.values()], ['workflow_a', 'workflow_b'])

    def test_add_group(self):
        config = SnakeParseConfig()
        # test adding more than one group
        config.add_group(name='G1', description='D1')
        config.add_group(name='G2', description='D2')
        self.assertEqual(len(config.groups), 2)

        # test failure with a snakefile with the same group if strict=True
        config.add_group(name='G2', description='D3', strict=False)
        self.assertEqual(config.groups['G2'], 'D3')
        with self.assertRaises(SnakeParseException):
            config.add_group(name='G2', description='D4', strict=True)
        self.assertEqual(config.groups['G2'], 'D3')

    ''' TODO: Tests for the __init__ method '''
