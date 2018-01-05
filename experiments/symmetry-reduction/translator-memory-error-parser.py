#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()

def parse_memory_error(content, props):
    translate_out_of_memory = False
    lines = content.split('\n')
    for line in lines:
        if line == 'MemoryError':
            translate_out_of_memory = True

    if translate_out_of_memory:
        exitcode = props['fast-downward_returncode']
        assert exitcode == 1
        unexplained_errors = set(props.get('unexplained_errors', []))
        error = props['error']
        assert len(unexplained_errors) <= 2
        assert 'critical-error' in unexplained_errors
        if len(unexplained_errors) == 2:
            assert 'output-to-run.err' in unexplained_errors
            unexplained_errors.remove('output-to-run.err')
        assert error == 'critical-error' or error == 'output-to-run.err'
        unexplained_errors.remove('critical-error')
        assert not len(unexplained_errors)
        del props['unexplained_errors']
        props['error'] = 'none'

parser.add_function(parse_memory_error, file='run.err')

parser.parse()
