#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

import sys

if (sys.version_info > (3, 0)):
    import subprocess
else:
    import subprocess32 as subprocess

from dl_model import selector

# TODO: better fallback than blind?
FALLBACK_COMMAND_LINE_OPTIONS = ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(blind,symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)']
IMAGE_CREATION_TIME_LIMIT = 180 # 300s

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

def build_planner_from_command_line_options(repo_dir, command_line_options):
    if len(command_line_options) == 1:
        assert command_line_options[0] == 'seq-opt-symba-1'
        planner = [sys.executable, os.path.join(repo_dir, 'symba.py'), command_line_options[0], domain, problem, plan]
    else:
        planner = [sys.executable, os.path.join(repo_dir, 'fast-downward.py'), '--transform-task', 'preprocess', '--build', 'release64', '--search-memory-limit', '7600M', '--plan-file', plan, domain, problem]
        planner.extend(command_line_options)
    return planner

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("domain_file")
    parser.add_argument("problem_file")
    parser.add_argument("plan_file")

    args = parser.parse_args()
    domain = args.domain_file
    problem = args.problem_file
    plan = args.plan_file

    repo_dir = get_repo_base()
    try:
        # Create an image from the abstract structure for the given domain and problem.
        image_dir = os.getcwd()
        subprocess.check_call([sys.executable, os.path.join(repo_dir, 'src/translate/create_image.py'), '--only-functions-from-initial-state', '--write-abstract-structure-image-reg', '--bolding-abstract-structure-image', '--abstract-structure-image-target-size', '128', '--image-output-directory', image_dir, domain, problem], timeout=IMAGE_CREATION_TIME_LIMIT)
        # TODO: we should be able to not hard-code the file name
        image_file_name = 'graph-gs-L-bolded-cs.png'
        image_path = os.path.join(image_dir, image_file_name)
        assert os.path.exists(image_path)
        # Use the learned model to select the appropriate planner (its command line options)
        json_model = os.path.join(repo_dir, 'dl_model/model.json')
        h5_model = os.path.join(repo_dir, 'dl_model/model.h5')
        command_line_options = selector.compute_command_line_options(json_model, h5_model, image_path)
        print("Command line options from model: {}".format(command_line_options))
    except:
        # Image creation failed, e.g. due to reaching the time limit
        print()
        print("Image creation failed, switching to fallback!")
        print()
        command_line_options = FALLBACK_COMMAND_LINE_OPTIONS

    # Build the planner call from the command line options computed above.
    planner = build_planner_from_command_line_options(repo_dir, command_line_options)
    try:
        print("Planner call string: {}".format(planner))
        subprocess.call(planner)
    except:
        # TODO: make the type of exception more precise, otherwise killing this
        # script from outside will not actually kill it.
        # Execution of the planner failed, e.g. due to the h2 preprocessor in conjunction with some heuristics.
        print()
        print("Planner failed, switching to fallback!")
        print()
        planner = build_planner_from_command_line_options(repo_dir, FALLBACK_COMMAND_LINE_OPTIONS)
        print("Planner call string: {}".format(planner))
        subprocess.call(planner)
