    #!/usr/bin/env bash

###############################################################################
# Script that should be run pre-commit after making any changes.
#
# Runs:
#   Unit tests
#   Linting
#   Type checking
###############################################################################

set -euo pipefail

failures=""

function banner() {
	echo
	echo "================================================================================"
	printf "$*\n"
	echo "================================================================================"
	echo
}

#####################################################################
# Takes two parameters, a "name" and a "command".
# Runs the command and prints out whether it succeeded or failed, and
# also tracks a list of failed steps in $failures.
#####################################################################
function run() {
    local name=$1
    local cmd=$2

    banner "Running $name\n    $cmd"
    set +e
    $cmd
    exit_code=$?
    set -e

    if [[ $exit_code == 0 ]]; then
        echo Passed $name
    else
        echo Failed $name
		failures="$failures\n    $name";
    fi
}


function pass_or_fail() {
	local message=$1
	local exit_code=$2

	if [ $exit_code == 0 ]; then
		echo Passed $message
	else
		echo Failed $message
		failed_tests=true
	fi
}

curdir=$(cd $(dirname $0) && pwd -P)
root=$(cd $(dirname $(dirname ${curdir})) && pwd -P)

pushd $root > /dev/null
run "Unit Tests" "coverage run -m unittest discover -s ${root}/src"
run "Linting"       "flake8 --count --config=${curdir}/flake.cfg ${root}/src/snakeparse"
pushd ${root}/src > /dev/null
run "Type Checking" "mypy -p snakeparse --config ${curdir}/mypy.ini"
popd > /dev/null

if [ -z "$failures" ]; then
    banner "Passed"
else
    banner "Failed with failures in: $failures"
    exit 1
fi
