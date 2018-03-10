# Author: Nils Homer <nilshomer@gmail.com>.

'''Command-line parsing library for Snakemake

This module allows multiple Snakemake workflows to be combined into one command
line interface.  Arguments to Snakemake and workflow-specific arguments are
supported.

This module is inspired by tool-chains like fgbio, Picard, and samtools, that:

    - support multiple tools which all can be specified on the same command line
    - combines the argument parsing from all tools into one command line
    - supports dispatching the tool-specific arguments to sub-parsers
    - enable argument parsing for the tool-chain, that can propogate to all
      tools; in this case, arugenets for Snakemake.

The following is a minimumal usage example for how to use the API:
    SnakeParse(args=sys.argv[1:]).run()

The magic comes from creating a configuration object ('SnakeParseConfig') that
configures the paths to where the Snakemake files (snakefiles) and optionally
associated SnakeParse files live, as well as various options for how workflows
are displayed on the command line.  Once the configuration object has been
created, it's as simple as:

    SnakeParse(args=sys.argv[1:], config=config)

The given arguments may contain the argument separator '--'.  All arguments
prior will be passed to Snakemake, while all arguments after will be passed to
the specified workflow.  Which workflow to run is determined as follows:

    1. If the argument separator is present, then if there is only one workflow
        configured, use that one, otherwise, assume the name of the workflow is
        specified immediate after the argument separator.
    2. If the argument separator is not present, search for the first argument
        that matches a known workflow name.

If no workflows are configured, but the '-s/--snakefile' option is given before
the argument separator, then this workflow is added to the list of workflows,
and that workflow will be executed.

For a more typical example, suppose the path to the the snakefiles is
'~/snakemake-workflows', and that for each snakefile, a corresponding
SnakeParse file exists in the same directory but with extension from the
snakefile replaced with '_snakeparser.py'.  Then the following will work:

   config = SnakeParseConfig(snakefile_globs='~/snakemake-workflows/*')
   SnakeParse(args=sys.argv[1:], config=config).run()

Below are some example argument lists.  Suppose the workflow named 'Example' has
a single required command line option '--message' that takes a message to be
printed.

For running a single workflow:
   args = ['--snakefile', '/path/to/snakefile', '--', '--message', 'Hello!']

If a single workflow has been added via SnakeParseConfig object:

   args = ['Example', '--message', 'Hello!']

Alternatively, the workflow name can be omitted when only one workflow has been
configured:

   args = ['--', '--message', 'Hello!']

If multiple workflows are configured, then the name must be explictly used.

In some cases, the options to Snakemake take multiple values, so it is ambiguous
where the arguments to Snakemake end and the arguments to the workflow begin.
Use the '--' argument to explicitly seperate the two lists.  The workflow name
should be immediately after the '--' seperator:

    args = ['--force-run', 'rule-1', 'rule-2', '--', 'Example', '--message', 'Hello!']]

In the above example, the arguments ['--force-run', 'rule-1', 'rule-2'] are
passed to Snakemake, while the arguments ['--message', 'Hello!'] are passed to
the SnakeParser for the Example workflow.

Ther are two ways for your snakefile source to receive the parsed arguments: (1)
define a concrete subclass of SnakeParse, or (2) define a method
'snakeparser(**kwargs)' that returns a concrete sub-class of SnakeParse.  For
convenience when implementing parsing using the argparse module, the class
snakeparse.api.SnakeArgumentParser can be used for (1), while the method
snakeparse.api.argparser can be used for (2).  For the Example workflow above,
an example implementation with a concrete class definition is as follows:

    from snakeparse.api import SnakeArgumentParser
    class Parser(SnakeArgumentParser):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.parser.add_argument('--message', help='The message.', required=True)

Alternatively, a method can be defined in 'example_snakeparser.py'

    from snakeparse.parser import argparser
    def snakeparser(**kwargs):
        p = argparser(**kwargs)
        p.parser.add_argument('--message', help='The message.', required=True)
        return p

The module contains the following public classes:

    - SnakeParser -- The abstract base class that implements the workflow
        specific argument parsing.  This parser will be invoked by SnakeParse
        prior to running Snakemake, to ensure that the command line arguments
        are specified correctly.  This parser is likely also used in the
        Snakemake file to re-instantiate the parsed arguments.

    - SnakeArgumentParser -- The abstract base class to help argument parsers
        that use python's argparse module.

    - SnakeParseException -- The exception raised by this module.

    - SnakeParseWorkflow -- A container class for basic meta information about
        a supported workflow, including to but not limited to the name dispalyed
        on the command line, the paths to the snakefile and SnakeParse file, a
        workflow group to which this workflow belongs, and a short description
        to display on the commad line.

    - SnakeParseConfig -- The class used to configure SnakeParse.  In
        particular, where workflows are located (if they are to be discovered),
        definitions for the workflow (if they are to be explicitly defined),
        where SnakeParse files live (either generally or relative to the
        Snakemake files), the names of the workflow groups, and other
        miscellaneous options.

    - SnakeParse -- The main entry point for command-line parsing for Snakemake.
        The configuration for SnakeParse will be optionally loaded, then the
        workflow to run will be parsed, then the workflow arguments will be
        parsed, and finally the workflow will be run along with all the
        Snakemake specific arguments.

All other classes in this module are considered implementation details.
'''

import os
import sys
import json
import yaml
import pyhocon
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict
import tempfile
import importlib.util
import inspect
import argparse
from abc import ABC, abstractmethod
from .version import __version__
import shutil
import subprocess
import snakemake.parser as snakemake_parser


class _ArgumentParser(argparse.ArgumentParser):
    ''' A custom argument parser that gives the reason why an error occured.
        Also changes the title of the optional aguments from 'optional arguments'
        to 'Optional options'.  Also, by default the print_help method will not
        do anything (i.e. print the help message).  This is so that it will only
        be displayed when snakeparse wishes.
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._optionals.title = 'Optional options'

    def print_help(self, file = None, suppress: bool = True):
        if not suppress:
            super().print_help(file=file)

    def error(self, message: str):
        ''' Raises an SnakeParseException with the given message.'''
        #self.print_help()
        #self.file.write('\nerror: %s\n' % message)
        #sys.exit(2)
        raise SnakeParseException(message)


class SnakeParser(ABC):
    '''The abstract base class for implementing the workflow specific argument
    parsing.
    '''

    '''Character that prefix files containing additional arguments.'''
    FROMFILE_PREFIX_CHARS = '@'

    def __init__(self, **kwargs):
        self._group = None
        self._description = None

    @abstractmethod
    def parse_args(self, args: List[str]) -> Any:
        '''Parses the command line arguments.'''

    @abstractmethod
    def parse_args_file(self, args_file: Path) -> Any:
        '''Parses command line arguments from an arguments file'''

    def parse_config(self, config: dict) -> Any:
        '''Parses arguments from a Snakemake config object.  It is assumed the
        arguments are contained in an arguments file, whose path is stored in
        the config with key SnakeParse.ARGUMENT_FILE_NAME_KEY.'''
        args_file = config[SnakeParse.ARGUMENT_FILE_NAME_KEY]
        if args_file is not None:
            args_file = Path(config[SnakeParse.ARGUMENT_FILE_NAME_KEY])
            return self.parse_args_file(args_file=args_file)
        else:
            try:
                return self.parse_args('')
            except SnakeParseException:
                return argparse.Namespace()

    @abstractmethod
    def print_help(self, file=None) -> None:
        '''Prints the help message'''

    @property
    def group(self):
        '''The name of the workflow group to which this group belongs.'''
        return self._group

    @group.setter
    def group(self, value):
        self._group = value

    @group.deleter
    def group(self):
        self._group = None

    @property
    def description(self):
        '''A short description of the workflow, used when listing the
        workflows.
        '''
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @description.deleter
    def description(self):
        self._description = None


class SnakeArgumentParser(SnakeParser):
    '''The abstract base class to help argument parsers that use python's
    argparse module.  Keyword arguments will be passed to the argument
    parser's constructor. '''

    @abstractmethod
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser = _ArgumentParser(fromfile_prefix_chars=SnakeParser.FROMFILE_PREFIX_CHARS, **kwargs)

    def parse_args(self, args) -> Any:
        '''Parses the command line arguments.'''
        return self.parser.parse_args(args=args)

    def parse_args_file(self, args_file: Path) -> Any:
        '''Parses command line arguments from an arguments file'''
        return self.parse_args(args=['@' + str(args_file)])

    def print_help(self, file=None) -> None:
        '''Prints the help message'''
        self.parser.print_help(suppress=False, file=file)


class SnakeParseException(Exception):
    '''The exception raised by classes in this module.'''
    pass


class SnakeParseWorkflow(object):
    '''A container class for basic meta information about a workflow to be
    included on the command line.

    Keyword Arguments:
        - name -- The canonical name of the workflow displayed on the command
            line.
        - snakefile -- The path to the snakefile file.
        - group -- The name of the workflow group, used to group workflows on
            the command line.
        - description - A short description of the workflow, used when listing
            the workflows.
    '''

    def __init__(self,
                 name: str,
                 snakefile: Path,
                 group: Optional[str] = None,
                 description: Optional[str] = None):
        self.name        = name
        self.snakefile   = snakefile
        self.group       = group
        self.description = description
        if not self.snakefile.exists():
            raise SnakeParseException(f'Snakefile does not exists: {self.snakefile}')


class SnakeParseConfig(object):
    '''The class used to configure SnakeParse.

    Keyword Arguments:
        - config_path -- The path to the SnakeParse configuration file, in JSON,
            YAML, or HOCON format.  Details of its contents are described below.
        - prog -- The name of the tool-chain.
        - snakemake -- the optional path to the Snakemake executable.
        - name_transform -- An optional method to transform the basename of a
            workflow's snakefile to the canonical name to use on the command
            line.
        - parent_dir_is_group_name -- True to use the parent directory of the
            workflow's snakefile as the workflow's group name.  Only applied
            when searching directories for snakefiles, or when group name is not
            explicitly given.
        - workflows -- optionally, the list of workflows as
            SnakeParseWorkflow objects.
        - groups - optionally, one or more key-value pairs, with the key being
            the canonical workflow group name, and the value being a
            description for that group to display on the command line.
        - snakefile_globs -- optionally, or more glob strings specifying
            where snakefile files can be found.

    NB: the values in the configuration file take precedence over the keyword
    arguments.  In particular, the configuration file may override Worfklows
    given in the 'workflows' keyword argument.

    Configuration paths (in HOCON paths):

        - snakemake -- the optional path to the Snakemake executable.
        - prog -- the optional name of the tool-chain.
        - name_transform -- alias for a built-in method to produce the
            workflow's name (see the similarly named keyword argument). Either
            'snake_to_camel' or 'camel_to_snake' for converting from Snake case
            to Camel case, or vice versa.
        - parent_dir_is_group_name -- optional; see the similarly named
            keyword argument.
        - workflows -- optionally, a list of configuration objects, one per
            workflow specified.  They object key should be the canonical
            workflow name to be displayed on the command line, with a dictionary
            of key value pairs specifying the wofklow configuration with the
            same names as SnakeParseWorkflow (snakefile, group, and
            description).  Only the snakefile key-value pair is required.
        - groups - optional; see the similarly named keyword argument.
        - snakefile_globs -- optional; see the similarly named keyword argument.
    '''

    def __init__(self,
                 config_path: Optional[Path]=None,
                 prog: str=None,
                 snakemake: Path=None,
                 name_transform=None,
                 parent_dir_is_group_name: bool=True,
                 workflows: Dict[str, 'SnakeParseWorkflow'] = OrderedDict(),
                 groups: Dict[str, str] = OrderedDict(),
                 snakefile_globs: Optional[List[str]] = []):
        self.prog                     = prog
        self.snakemake                = snakemake
        self.name_transform           = name_transform
        self.parent_dir_is_group_name = parent_dir_is_group_name
        self.workflows                = workflows
        self.groups                   = groups

        if config_path is None:
            data = OrderedDict()
        else:
            # Load the JSON configuration data
            with config_path.open('r') as fh:
                name = config_path.name
                if name.endswith('.json'):
                    data = json.loads(fh.read(), object_pairs_hook=OrderedDict)
                elif name.endswith('.yaml') or name.endswith('.yml'):
                    data = yaml.load(fh)
                else:
                    try:
                        data = pyhocon.ConfigFactory.parse_string(content=fh.read())
                    except pyhocon.exceptions.ConfigException as e:
                        if name.endswith('.conf'):
                            raise e
                        raise SnakeParseException(f"Don't know how to open a {config_path.suffix} config file: {config_path}")

        ''' Basic conciguration '''

        # configure Snakemake
        if 'snakemake' in data:
            self.snakemake = Path(data['snakemake'])

        if 'prog' in data:
            self.prog = data['prog']

        # Configure how we transform the snakefile file name to the workflow name
        if 'name_transform' in data:
            if name_transform is not None:
                raise SnakeParseException("name_transform parameter given but found 'name_transform' in {config_path}")
            self.name_transform = self.name_transfrom_from(data['name_transform'])

        # This controls if the workflows group attribute should be set to
        # the parent directory of the snakefile
        if 'parent_dir_is_group_name' in data:
            v = data['parent_dir_is_group_name']
            self.parent_dir_is_group_name = v.lower() in ['true', 't', 'yes', 'y']
        else:
            self.parent_dir_is_group_name = False

        def paths_from(maybe_glob: str) -> Tuple[Path, str]:
            if maybe_glob.startswith('/'):
                glob_root = Path('/')
                glob = maybe_glob[1:]
            else:
                glob_root = Path('.')
                glob = maybe_glob
            paths = [p for p in glob_root.glob(glob)]
            if not paths:
                raise SnakeParseException(f"No paths found from glob '{maybe_glob}'")
            return paths

        # Add all the workflows via the snakefile_globs
        if 'snakefile_globs' in data:
            snakefile_globs.extend(data['snakefile_globs'])
        for maybe_glob in snakefile_globs:
            for snakefile in paths_from(maybe_glob=maybe_glob):
                self.add_snakefile(snakefile=snakefile)

        # Configure workflows explicitly
        if 'workflows' in data:
            workflows = data['workflows']
            if not isinstance(workflows, list):
                raise SnakeParseException(f"Expected a list of workflows at 'workflows' in {config_path}")

            # check that no names are found twice
            names = list(workflows.keys())
            duplicates = set([name for name in names if names.count(name) > 1])
            if duplicates:
                duplicate_names = ", ".join(duplicates)
                raise SnakeParseException(f"Found multiple workflows with the same name '{duplicate_names}' in {config_path}")

            for name in workflows:
                workflow_data = workflows[name]

                # if the workflow exists, overwrite the values
                existing_workflow = self.workflows.get(name)
                def get_existing(key):
                    return None if existing_workflow is None else geattr(existing_workflow, key)

                # Set the defaults to the existing workflows, if any
                snakefile   = get_existing('snakefile')
                group       = get_existing('group')
                description = get_existing('description')

                # snakefile
                if 'snakefile' in workflow_data:
                    snakefile = Path(workflow_data['snakefile'])
                else:
                    raise SnakeParseException(f"No snakefile given for workflow with name '{name}' in {config_path}")

                # group
                if 'group' in workflow_data:
                    group = workflow_data['group']
                elif group is None and self.parent_dir_is_group_name:
                    group = snakefile.parent.name
                # remember to add the group (if defined) to the list of groups
                if group is not None:
                    self.groups[group] = None

                # description
                description = workflow_data['description'] if 'description' in workflow_data else description

                # build the workflow
                workflow = SnakeParseWorkflow(name=name, snakefile=snakefile, group=group, description=description)
                self.workflows[name] = workflow

        # Next, load the group and description from the snakeparse files, if the
        # former values are not set.
        for wf in self.workflows.values():
            if wf.group is not None and wf.description is not None:
                continue
            parser = self.parser_from(workflow=wf)
            if parser.group is not None:
                wf.group = parser.group
            if parser.description is not None:
                wf.description = parser.description

        # sort the workflows by group, then name
        self.workflows = OrderedDict([(wf.name, wf) for wf in sorted(self.workflows.values(), key=lambda wf: (str(wf.group), wf.name))])

        # Add the description for each group
        if 'groups' in data:
            self.groups[group] = data['groups']

    def add_workflow(self, workflow: SnakeParseWorkflow) -> 'SnakeParseConfig':
        '''Adds the workflow to the list of workflows.  A workflow with the same
        name should not exist.'''
        if workflow.name in self.workflows:
            raise SnakeParseException(f"Multiple workflows with name '{workflow.name}'.")
        self.workflows[workflow.name] = workflow
        return workflow

    def add_snakefile(self, snakefile: Path) -> 'SnakeParseConfig':
        '''Adds a new workflow with the given snakefile. A workflow with the
        same name should not exist.'''
        name        = snakefile.with_suffix('').name
        if self.name_transform is not None:
            name = self.name_transform(name)
        snakefile   = snakefile
        # FIXME: set group and description from the parser
        group       = snakefile.parent.name if self.parent_dir_is_group_name else None
        description = None
        if name in self.workflows:
            raise SnakeParseException(f"Multiple workflows with name '{name}'.")
        workflow = SnakeParseWorkflow(name=name, snakefile=snakefile, group=group, description=description)
        return self.add_workflow(workflow=workflow)

    def add_group(self, name: str, description: str, strict: bool = True) -> 'SnakeParseConfig':
        '''Adds a new group with the given name and description.  If strict is
        True, then no group with the same name should already exist. '''
        if strict and name in self.groups:
            raise SnakeParseException(f"Group '{name}' already defined")
        self.groups[name] = description
        return self

    @staticmethod
    def name_transfrom_from(key):
        '''Returns the built-in method to format the workflow's name.  Should be
        either 'snake_to_camel' or 'camel_to_snake' for converting from Snake case
        to Camel case, or vice versa.
        '''
        if key is None:
            return None
        elif key == 'snake_to_camel':
            return SnakeParseConfig._snake_to_camel
        elif key == 'camel_to_snake':
            return SnakeParseConfig._camel_to_snake
        else:
            raise SnakeParseException(f"Unknown 'name_transform': {key}")

    @staticmethod
    def _snake_to_camel(snake_str: str) -> str:
        '''Converts a string in Snake case to Camel case.'''
        return ''.join([s.title() for s in snake_str.split('_')])

    @staticmethod
    def _camel_to_snake(camel_str: str) -> str:
        '''Converts a string in Camel case to Snake case.'''
        if not camel_str:
            return camel_str
        first_char = camel_str[0].lower()
        return first_char + ''.join(['_' + c.lower() if c.isupper() else c for c in camel_str[1:]])

    @staticmethod
    def parser_from(workflow: 'SnakeParseWorkflow') -> SnakeParser:
        '''Builds the SnakeParser for the given workflow'''

        # Insert the directory containing the snakefile file so that relative
        # imports work and imports in the snakefile directory
        parent_module_name = str(workflow.snakefile.resolve().parent)
        sys.path.insert(0, parent_module_name)

        exec_exception = None

        # Compile and execute it!
        with workflow.snakefile.open('r') as fh:
            from snakemake.parser import parse
            from snakemake.workflow import Workflow

            snakefile = str(workflow.snakefile)

            # create a config with an undefined argument file so that parsing is skipped
            global config
            config = dict([(SnakeParse.ARGUMENT_FILE_NAME_KEY, None)])
            # add the config to a globals copy
            globals_copy = dict(globals())
            globals_copy['config'] = dict([(SnakeParse.ARGUMENT_FILE_NAME_KEY, None)])
            # parsing with snakemake requires there to be a global workflow object
            globals_copy['workflow'] = Workflow(snakefile=snakefile)

            # compile the snakefile using snakemake's parse method
            code, linemap, rulecount = snakemake_parser.parse(snakefile)
            code = compile(code, snakefile, 'exec')
            try:
                exec(code, globals_copy)
            except AttributeError as e:
                # in the case of required parser arguments, we may get some type
                # of exception
                #if not str(e).startswith("'Namespace'"):
                #    raise e
                exec_exception = SnakeParseException(f'Could not compile {snakefile}', e)

        classes = [obj for key, obj in globals_copy.items() if inspect.isclass(obj) and not inspect.isabstract(obj) and SnakeParser in inspect.getmro(obj)]
        methods = [obj for key, obj in globals_copy.items() if key == 'snakeparser' and inspect.isfunction(obj)]
        if len(classes) + len(methods) == 0:
            raise SnakeParseException(f'Could not find either a concrete subclass of SnakeParser or a method named snakeparser in {workflow.snakefile}', exec_exception)
        elif len(classes) + len(methods) > 1:
            raise SnakeParseException(f'Found {len(classes)} concrete subclasses of SnakeParser and {len(methods)} methods named snakeparser in {workflow.snakefile}', exec_exception)
        elif len(classes) == 1 and len(methods) == 0:
            parser_class = classes[0]
            if issubclass(parser_class, SnakeArgumentParser):
                return parser_class(usage=argparse.SUPPRESS)
            else:
                return parser_class()
        else:
            assert len(classes) == 0 and len(methods) == 1, f'Bug: {len(classes)} != 0 and {len(methods)} != 1'
            parser_method = methods[0]
            parser = parser_method()
            if issubclass(parser.__class__, SnakeArgumentParser):
                return parser_method(usage=argparse.SUPPRESS)
            else:
                return parser

    @staticmethod
    def config_parser(usage = argparse.SUPPRESS) -> argparse.ArgumentParser:
        '''Returns an argparse.ArgumentParser for the configuration options'''

        # An argument parser that doesn't exit
        class _ConfigParser(_ArgumentParser):
            def exit(self, status=0, message=None):
                raise SnakeParseException(message)
        parser = _ConfigParser(usage=usage, allow_abbrev=False)
        parser.add_argument('--config',
            help='The path to the snakeparse configuration file (can be JSON, YAML, or HOCON).',
            type=Path)
        parser.add_argument('--snakefile-globs',
            help='Optionally, or more glob strings specifying where SnakeMake (snakefile) files can be found',
            nargs='*',
            default=[])
        parser.add_argument('--prog',
            help='The name of the tool-chain to use ont the command-line',
            default='snakeparse')
        parser.add_argument('--snakemake',
            help='The path to the snakemake executable, otherwise it should be on the system path',
            type=Path)
        parser.add_argument('--name-transform',
            help='Transform the name of the workflow from Snake case to Camel case ("snake_to_camel") or vice versa ("camel_to_snake")',
            default='snake_to_camel')
        parser.add_argument('--parent-dir-is-group-name',
            help='In the last resort if no group name is found, use the name of the parent directory of the snakefile as the group name',
            type=bool,
            default=False)
        parser.add_argument('--extra-help',
            help='Produce help with extra debugging information',
            type=bool,
            default=False)
        return parser


class SnakeParse(object):
    '''The main entry point for command-line parsing for Snakemake.

    Keyword Arguments:
        - args -- The list of command line arguments.
        - config -- Optionally a SnakeParse configuration object.
        - prog -- Optionally the name of the tool-chain to display in the usage.
        - file -- Optionally the file to write any error or help messages, defaults to sys.stdout.
    '''

    '''The default key to use in Snakemake's config dictionary.'''
    ARGUMENT_FILE_NAME_KEY = 'snakeparse_args_file'

    def __init__(self,
                 args: List[str]=[],
                 config: Optional['SnakeParseConfig']=None,
                 debug: bool = False,
                 file = sys.stdout):
        self.config = config
        self.debug  = debug
        self.file   = file

        '''
        If no config was given, try parsing the args.
        ------------------------------------------------------------------------
        First check to see if the config file specifies them, otherwise search
        the args for the '-s/--snakefile' argument (must be before any
        occurrence of '--').  Next check if the workflow name is after the '--'.
        '''
        if self.config is None:
            # Dummy value in case a usage is needed.
            self.config = SnakeParseConfig()

            # parse the leading arguments until an unknonwn argument is found or no more
            # arguments exist.  Prepend an arg for argparse to work.
            try:
                args_end, config_args = self._parse_known_args(args=args, parser=SnakeParseConfig.config_parser(usage=SnakeParse.usage_short()))
                remaining_args = args[args_end:]
            except SnakeParseException as e:
                self._usage(message=str(e))
                sys.exit(2)

            # Check if we should print the help
            if (len(remaining_args) == 1 and args[-1] in ['--help', '-h']) or len(args) == 1:
                self._usage(message=None)
                sys.exit(2)

            # Create the config
            self.config = SnakeParseConfig(
                config_path              = config_args.config,
                prog                     = config_args.prog,
                snakemake                = config_args.snakemake,
                name_transform           = SnakeParseConfig.name_transfrom_from(config_args.name_transform),
                parent_dir_is_group_name = config_args.parent_dir_is_group_name,
                snakefile_globs          = config_args.snakefile_globs
            )

            # Remove the arguments used by snakeparse
            args  = remaining_args
            debug = config_args.extra_help

        assert self.config is not None

        workflow_name = None
        snakemake_args_end = None
        workflow_args_start = None

        '''
        Add a Workflow if the -s/--snakefile Option was specified
        ------------------------------------------------------------------------
        First check to see if the config file specifies them, otherwise search
        the args for the '-s/--snakefile' argument (must be before any
        occurrence of '--').  Next check if the workflow name is after the '--'.
        '''
        has_snakefile_argument = False
        end = len(args)
        if '--' in args:
            end = args.index('--')
        snakefile = None
        for option in ['-s', '--snakefile']:
            if option in args[:end]:
                idx = args[:end].index(option)
                if idx + 1 < end:
                    snakefile = Path(args[idx+1])
                    has_snakefile_argument = True
                    break
        if snakefile is not None:
            workflow = self.config.add_snakefile(snakefile=snakefile)
            workflow_name = workflow.name
            snakemake_args_end = args.index(workflow_name)
            workflow_args_start = args.index(workflow_name) + 1
        if not self.config.workflows:
            self._usage('No workflows found.')

        '''
        Workflow to Execute
        ------------------------------------------------------------------------
        Find the name of the workflow to execute.  If we find '--' in args, then
        either we have one workflow (use its name), or the workflow name is the
        argument immediately after the '--'.  Otherwise, go through the
        available workflows, and find the first one whose name is in args.
        '''
        if workflow_name is not None:
            # already set above
            pass
        elif '--' in args:
            # Check if the workflow name is _after_ the '--'
            idx = args.index('--')
            if idx + 1 < len(args):
                name = args[idx+1]
                if name in self.config.workflows:
                    workflow_name = name
                    snakemake_args_end = idx
                    workflow_args_start = idx+2
            if workflow_name is None and  len(self.config.workflows) == 1:
                workflow_name  = list(self.config.workflows.keys())[0]
                snakemake_args_end = idx
                workflow_args_start = idx+1
        elif args:
            # find workflow name in args, use it
            for wf_name in self.config.workflows:
                if wf_name in args:
                    args_split_value    = wf_name
                    workflow_name       = wf_name
                    snakemake_args_end  = args.index(wf_name)
                    workflow_args_start = args.index(wf_name) + 1

        if workflow_name is None:
            # TODO: search in args for any similar workflow now and suggest it
            self._usage('No workflow given.')
        self.snakemake_args = args[:snakemake_args_end]
        workflow_args  = args[workflow_args_start:]

        '''
        Setup the Workflow to Run with Snakemake
        ------------------------------------------------------------------------
        1. Write the workflow arguments to a file.
        2. Try parsing the arguments in the file with the parser in the
           snakemake file.
        3. Add the Snakemake argument for the args file:
             --config <ARGUMENT_FILE_NAME_KEY>=<file>
        4. Add the Snakemake argument for the snakefile if necessary:
             --snakefile <workflow.snakefile>
        '''
        self.workflow = self.config.workflows[workflow_name]
        # 1. Write the workflow arguments to a file
        with tempfile.NamedTemporaryFile('w', suffix='.args.txt', delete=False) as fh:
            for arg in workflow_args:
                fh.write(arg + '\n')
            self.snakeparse_args_file = Path(fh.name)
        # 2. Parse with snakeparse
        self._parse_workflow_args(workflow=self.workflow, args_file=Path(self.snakeparse_args_file).resolve())
        # 3. Add the custom config argument.
        self.snakemake_args.extend(['--config', f"{SnakeParse.ARGUMENT_FILE_NAME_KEY}={self.snakeparse_args_file}"])
        # 4. Add the --snakefile argument if necessary
        if not has_snakefile_argument:
            self.snakemake_args.extend(['--snakefile', str(self.workflow.snakefile.resolve())])

    def run(self):
        '''Execute the Snakemake workflow'''
        snakemake = self.config.snakemake if self.config.snakemake else 'snakemake'
        retcode = subprocess.call([snakemake] + self.snakemake_args)
        self.snakeparse_args_file.unlink()
        sys.exit(retcode)

    def _parse_workflow_args(self, workflow: 'SnakeParseWorkflow', args_file: Path) -> None:
        '''Dynamically loads the module containing the workflow parser and
        attempts to parse the arguments in the given arguments file.

        The module must have a single concrete class implementing SnakeParser.
        '''
        parser = self.config.parser_from(workflow=workflow)
        try:
            parser.parse_args_file(args_file=args_file)
        except SnakeParseException as e:
            # error in specifying the argument
            self._print_workflow_help(workflow=workflow, parser=parser, message=str(e))
        except SystemExit:
            # most likely help
            self._print_workflow_help(workflow=workflow, parser=parser, message=None)

    def _print_workflow_help(self, workflow: 'SnakeParseWorkflow', parser: 'SnakeParser', message: Optional[str] = None) -> None:
        '''Prints the help message with all available workflows and the workflow
        specific help.'''
        self._usage(exit=False)
        self.file.write(f'\n{workflow.name} Arguments:\n')
        self._print_line()
        self.file.write('\n')
        # Next print the parser usage
        parser.print_help(file=self.file)
        # Next the message
        if message:
            self.file.write(f'\nerror: {message}')
        self.file.write('\n')
        sys.exit(2)

    @staticmethod
    def _parse_known_args(parser, args):
        '''Parses the args with the given parsers until an unknown argument is
        encountered.'''
        if not args:
            namespace, remaining = parser.parse_known_args(args=args)
            return 1, namespace
        namespace = argparse.Namespace()
        end = 1
        while end <= len(args):
            try:
                namespace, remaining = parser.parse_known_args(args=args[:end])
                if remaining:
                    return end-1, namespace
            except SnakeParseException:
                # Keep going, as we may require values in args
                pass

            end += 1
        return end, namespace

    def _usage_short(self, workflow_name=None):
        prog = self.config.prog if self.config is not None and self.config.prog is not None else "snakeparse"
        return self.usage_short(prog=prog, workflow_name=workflow_name)

    @staticmethod
    def usage_short(prog="snakeparse", workflow_name=None):
        '''A one line usage to dispaly at the top of any usage or help message.'''
        if workflow_name is None:
            workflow_name = '[workflow name]'
        return f'{prog} [snakeparse options] [snakemake options] {workflow_name} [workflow options]'.lstrip(' ')

    def _print_line(self):
        self.file.write(('-'*60) + '\n')

    def _usage(self, message: Optional[str] = None, exit: bool =True):
        '''The long usage that lists all the available workflows.'''
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        group_name_columns = 38 # includes the colon
        group_description_columns = terminal_size.columns - group_name_columns
        workflow_name_columns = group_name_columns - 3
        workflow_description_columns = group_description_columns - 1

        # Pre-amble
        self.file.write("Usage: " + self._usage_short() + '\n')
        self.file.write(f'Version: {__version__}\n\n')

        # SnakeParse help
        SnakeParseConfig.config_parser().print_help(suppress=False, file=self.file)

        # Print the workflows, grouped by group.
        if self.config.workflows:
            self.file.write('\nAvailable Workflows:\n')
            self._print_line()
            groups = OrderedDict(self.config.groups)
            for wf in self.config.workflows.values():
                if not wf.group in groups:
                    groups[wf.group] = None
            for group, desc in groups.items():
                name = ('Worfklows' if group is None else group) + ':'
                desc = '' if desc is None else desc
                self.file.write(f'{name:<{group_name_columns}}{desc:<{group_description_columns}}\n')
                for wf in self.config.workflows.values():
                    if wf.group != group:
                        continue
                    desc = str(wf.snakefile) if wf.description is None else wf.description
                    self.file.write(f'    {wf.name:<{workflow_name_columns}}{desc:<{workflow_description_columns}}\n')
                    if self.debug:
                        self.file.write(f'        snakefile:  {wf.snakefile}\n')
                self._print_line()
        else:
            self.file.write('\nNo workflows configured.\n')
            self._print_line()

        # Write the message
        if message is not None:
            self.file.write(f'\n{message}\n')
        if exit:
            sys.exit(2)
