#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from subprocess import call
import os
import sys
import timers

def get_script():
    """Get file name of main script."""
    return os.path.abspath(sys.argv[0])


def get_script_dir():
    """Get directory of main script.

    Usually a relative directory (depends on how it was called by the user.)"""
    return os.path.dirname(get_script())

def get_repo_base():
    """Get base directory of the repository, as an absolute path.

    Search upwards in the directory tree from the main script until a
    directory with a subdirectory named ".hg" is found.

    Abort if the repo base cannot be found."""
    path = os.path.abspath(get_script_dir())
    while os.path.dirname(path) != path:
        if os.path.exists(os.path.join(path, ".hg")):
            return path
        path = os.path.dirname(path)
    sys.exit("repo base could not be found")

parser = argparse.ArgumentParser()

parser.add_argument("config")
parser.add_argument("domain_file")
parser.add_argument("problem_file")
parser.add_argument("plan_file")

args = parser.parse_args()
config = args.config
domain = args.domain_file
problem = args.problem_file
plan_file = args.plan_file

repo_dir = get_repo_base()
planner = os.path.join(os.path.abspath(repo_dir), 'symba', 'src', 'plan-ipc')

timer = timers.Timer()
call([planner, config, domain, problem, plan_file])
print("Overall time: {}".format(timer))
