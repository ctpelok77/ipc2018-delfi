#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from subprocess import call
import os
import sys

from dl_model import selector

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

def force_remove_file(file_name):
    try:
        os.remove(file_name)
    except OSError:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("domain_file")
    parser.add_argument("problem_file")
    parser.add_argument("plan_file")

    args = parser.parse_args()
    domain = args.domain_file
    problem = args.problem_file
    plan = args.plan_file

    # TODO: limit time for the calls to subprocess (easiest probably to use python3.3+)
    # TODO: use fallback if everything fails
    # TODO: if something fails (like the problem with the h2 preprocessor), catch and repeat with a default config
    repo_dir = get_repo_base()
    print("repo dir: {}".format(repo_dir))
    print(os.listdir(repo_dir))

    # create image for given domain/problem
    call([os.path.join(repo_dir, 'src/translate/create_image.py'), '--only-functions-from-initial-state', '--write-abstract-structure-image-reg', '--bolding-abstract-structure-image', '--abstract-structure-image-target-size', '128', domain, problem])
    image_file_name = 'graph-gs-L-bolded-cs.png'
    image_path = os.path.join(repo_dir, image_file_name)
    print("image path {}".format(image_path))
    assert os.path.exists(image_path)

    print("repo dir: {}".format(repo_dir))
    print(os.listdir(repo_dir))

    print("pwd: {}".format(os.getcwd()))
    print(os.listdir(os.getcwd()))

    # use the learned model to select the appropriate planner (its command line options)
    json_model = os.path.join(repo_dir, 'dl_model/model.json')
    print("json_model path {}".format(json_model))
    h5_model = os.path.join(repo_dir, 'dl_model/model.h5')
    print("h5_model path {}".format(h5_model))
    command_line_options = selector.compute_command_line_options(json_model, h5_model, image_path)

    # build the correct command line to be called
    if len(command_line_options) == 1:
        assert command_line_options[0] == 'seq-opt-symba-1'
        planner = [sys.executable, 'symba.py', command_line_options[0], domain, problem, plan]
    else:
        planner = [sys.executable, 'fast-downward.py', '--transform-task', 'preprocess', '--build', 'release64', '--search-memory-limit', '7600M', '--plan-file', plan, domain, problem]
        planner.extend(command_line_options)
    print("Call string: {}".format(planner))
    print()
    call(planner)

    # Remove all files that possibly have been created
    force_remove_file(image_file_name)
    force_remove_file('output')
    force_remove_file('output.sas')
    force_remove_file('elapsed.time')
    force_remove_file('plan_numbers_and_cost')
    force_remove_file('sas_plan')
