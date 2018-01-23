# Import your custom parser
from write_message_snakeparser import Parser

# Get the arguments from the config file; this should always succeed.
args = Parser().parse_config(config=config)

rule all:
    input:
        'message.txt'

# A simple rule to write the message to the output
rule message:
    output: 'message.txt'
    shell: 'echo {args.message} > {output}'
