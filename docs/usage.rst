========
Examples
========

Snakeparse on the Command Line
==============================

To get started, run `snakeparse --help`.

Example
-------

1. [Using `argparse` and a custom method named snakeparser](https://github.com/nh13/snakeparse/blob/master/examples/argparse/method/README.md).
2. [Using `argparse` and a concrete sub-class of SnakeParser](https://github.com/nh13/snakeparse/blob/master/examples/argparse/class/README.md).

For more examples, see [this link](https://github.com/nh13/snakeparse/blob/master/examples/).

The example below is from (1).

Motivation
----------

Consider this simple Snakemake file (snakefile) that has a required configuration option:

```python
message = config['message']

rule all:
    input:
        'message.txt'

# A simple rule to write the message to the output
rule message:
    output: 'message.txt'
    shell: 'echo {message} > {output}'
```

You would need to run snakemake with the `--config` option:

```bash
snakemake --snakefile </path/to/snakefile> --config message='Hello World!'
```

If you forget to add the correct key/value pairs with the `--config` option, you'll get a `KeyError` exception, which is not user-friendly to non-programmers.
At that point, you're out of luck to see all the various required and optional config key/value pairs without examining the snakefile (i.e. you want to see a help message).
Have fun adding each configuration option one-by-one and gleaning their meaning.
Even examining the source, there needs to be clear documentation within your snakefile for each argument for the user to examine.
Why can't we just use [`argparse`](https://docs.python.org/3/library/argparse.html) as we normally would for our command-line python scripts?

Furthermore, if you have multiple snakefiles, setting the `--config` key/value pairs can get quite painful, notwithstanding the fact you need to specify the path to the specific snakefile your interested in each time.
Why can't we put all the snakefiles in one place, and have an easy way to specify which to run on the command line?
So many other command-line tools do it (ex. [`bwa`](https://github.com/lh3/bwa), [`samtools`](https://github.com/samtools/samtools), [`fgbio`](https://github.com/fulcrumgenomics/fgbio), [`Picard`](https://github.com/broadinstitute/picard/)), and even other workflow software do it (ex. [`dagr`](https://github.com/fulcrumgenomics/dagr/)), why can't we do it?

This is why I wrote Snakeparse.

Setup
-----

[`Source: examples/argparse/method/write_message.smk`](https://github.com/nh13/snakeparse/blob/master/examples/argparse/method/write_message.smk)

Modify the above snakefile by prepending the following:

```python
# Import the parser from snakeparse
from snakeparse.parser import argparser

def snakeparser(**kwargs):
    ''' The method that returns the parser with all arguments added. '''
    p = argparser(**kwargs)
    p.parser.add_argument('--message', help='The message.', required=True)
    return p

# Get the arguments from the config file; this should always succeed.
args = snakeparser().parse_config(config=config)

# NB: you could use `args.message` directly.
message = args.message
```

Execution
---------

Snakeparse Command Line Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can run the installed `snakeparse` utility as follows:

```snakeparse --snakefile examples/argparse/method/write_message.smk -- --message 'Hello World!'```

or

```snakeparse --snakefile-globs examples/argparse/method/*smk -- WriteMessage --message 'Hello World!'```

Programmatic Execution
~~~~~~~~~~~~~~~~~~~~~~

```python
config = SnakeParseConfig(snakefile_globs='~/examples/argparse/method/*smk')
SnakeParse(args=sys.argv[1:], config=config).run()
```

or alternatively `SnakeParse` accepts leading configuration arguments:

```python
args = ['--snakefile-globs', '~/examples/argparse/method/*smk'] + sys.argv[1:]
SnakeParse(args=args, config=config).run()
```