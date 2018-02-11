#! /usr/bin/env python

import normalize
import options
import os
import pddl_parser
from abstract_structure_module import AbstractStructureGraph
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

if __name__ == "__main__":
    timer = timers.Timer()

    only_object_symmetries = options.only_object_symmetries
    stabilize_initial_state = not options.do_not_stabilize_initial_state
    stabilize_goal = not options.do_not_stabilize_goal

    use_bolding = options.bolding_abstract_structure_image
    write_original_size = options.write_abstract_structure_image_original_size
    abstract_structure_image_target_size = options.abstract_structure_image_target_size

    with timers.timing("Parsing pddl..", True):
        task = pddl_parser.open()
    with timers.timing("Normalizing task..", True):
        normalize.normalize(task)
    #print("Dumping task..")
    #task.dump()
    with timers.timing("Creating abstract structure graph..", True):
        graph = AbstractStructureGraph(task, only_object_symmetries, stabilize_initial_state, stabilize_goal)
    if options.dump_dot_graph:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f, hide_equal_predicates=True)
        f.close()
    repo_dir = get_repo_base()
    if options.write_abstract_structure_image_raw:
        with timers.timing("Writing abstract structure graph raw image..", True):
            graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=1, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size, output_directory=repo_dir)
    if options.write_abstract_structure_image_reg:
        with timers.timing("Writing abstract structure graph grayscale 8bit image..", True):
            graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=3, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size, output_directory=repo_dir)
    if options.write_abstract_structure_image_int:
        with timers.timing("Writing abstract structure graph grayscale 32bit image..", True):
            graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=6, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size, output_directory=repo_dir)

    print("Done! %s" % timer)

    sys.stdout.flush()

