#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries_module import SymmetryGraph
import sys

WRITE_DOT_GRAPH = False
WRITE_MATRIX_IMAGE_RAW = True
WRITE_MATRIX_IMAGE_RAW = False
WRITE_MATRIX_IMAGE_REG = True
#WRITE_MATRIX_IMAGE_REG = False
WRITE_MATRIX_IMAGE_INT = True
WRITE_MATRIX_IMAGE_INT = False
USE_BOLDING = True
FIND_AUTOMORPHISMS = False

if __name__ == "__main__":
    only_object_symmetries = options.only_object_symmetries
    stabilize_initial_state = not options.do_not_stabilize_initial_state
    stabilize_goal = not options.do_not_stabilize_goal
    time_limit = options.bliss_time_limit
    print("Parsing pddl..")
    task = pddl_parser.open()
    print("Normalizing task..")
    normalize.normalize(task)
    #print("Dumping task..")
    #task.dump()
    print("Creating symmetry graph..")
    graph = SymmetryGraph(task, only_object_symmetries, stabilize_initial_state, stabilize_goal)
    if options.add_mutex_groups:
        print("cannot add mutex groups -- translator is not run!")
        exit(1)
    if WRITE_DOT_GRAPH:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f, hide_equal_predicates=True)
        f.close()
    if WRITE_MATRIX_IMAGE_RAW:
        print("Writing symmetry graph raw image..")
        graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=1, bolded=USE_BOLDING)
    if WRITE_MATRIX_IMAGE_REG:
        print("Writing symmetry graph 255 image..")
        graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=3, bolded=USE_BOLDING)
    if WRITE_MATRIX_IMAGE_INT:
        print("Writing symmetry graph int image..")
        graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=6, bolded=USE_BOLDING)

    if FIND_AUTOMORPHISMS:
        automorphisms = graph.find_automorphisms(time_limit)
        graph.write_or_print_automorphisms(automorphisms, hide_equal_predicates=True, write=False, dump=False)
    sys.stdout.flush()

