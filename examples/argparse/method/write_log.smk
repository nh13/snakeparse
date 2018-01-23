# Import your custom parser
from write_log_snakeparser import snakeparser

# Get the arguments from the config file; this should always succeed.
args = snakeparser().parse_config(config=config)

rule all:
    input:
        'log.txt'

# A simple rule to write the message to the output
rule message:
    output: 'log.txt'
    shell: 'echo {args.message} > {output}'
