#!/bin/bash

function demo_command()
{ local command=$1;
	clear
	echo -n "\$ "
	echo -n "$command" | pv -qL 15
	sleep 1
	echo "";
	eval $command
	echo -n "\$ "
	sleep 3
}

rm -v message.txt
clear
echo -n "\$ "
sleep 10
demo_command "snakeparse -h"
demo_command "ls -1 examples/argparse/method/*.smk"
demo_command "snakeparse --snakefile-globs examples/argparse/method/*.smk"
demo_command "snakeparse --snakefile-globs examples/argparse/method/*.smk -- WriteMessage -h"
demo_command "snakeparse --snakefile-globs examples/argparse/method/*.smk -- WriteMessage --message 'Hello World!'"
demo_command "cat message.txt"
demo_command "echo \"Enjoy!\""
