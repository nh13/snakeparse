import sys
from contextlib import contextmanager
from io import StringIO
from typing import List
from typing import Generator


@contextmanager
def captured_output_streams() -> Generator:
    '''Captures stderr and stdout and returns them'''
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def captured_output_to_str(output: StringIO, lines: bool = False) -> List[str]:
    retval: str = output.getvalue().rstrip('\r\n')
    return retval.split('\n') if lines else []
