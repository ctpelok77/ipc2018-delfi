#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries_module import SymmetryGraph
import sys

WRITE_DOT_GRAPH = True
WRITE_MATRIX_IMAGE = True
WRITE_MATRIX_IMAGE_RAW = True
WRITE_MATRIX_REPRESENTATION = False

if __name__ == "__main__":
    only_object_symmetries = options.only_object_symmetries
    stabilize_initial_state = not options.do_not_stabilize_initial_state
    stabilize_goal = not options.do_not_stabilize_goal
    time_limit = options.bliss_time_limit
    print("Parsing pddl..")
    task = pddl_parser.open()
    print("Normalizing task..")
    normalize.normalize(task)
    print("Dumping task..")
    task.dump()
    print("Creating symmetry graph..")
    graph = SymmetryGraph(task, only_object_symmetries, stabilize_initial_state, stabilize_goal)
    if options.add_mutex_groups:
        print("cannot add mutex groups -- translator is not run!")
        exit(1)
    if WRITE_DOT_GRAPH:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f, hide_equal_predicates=True)
        f.close()
    if WRITE_MATRIX_REPRESENTATION:
        print("Writing symmetry graph representation as a matrix..")
        f = open('out.matrix', 'w')
        graph.write_matrix_representation_raw(f, hide_equal_predicates=True)
        f.close()
    if WRITE_MATRIX_IMAGE:
        print("Writing symmetry graph image..")
        graph.write_matrix_image_gen(hide_equal_predicates=True, image_size=256)
    if WRITE_MATRIX_IMAGE_RAW:
        print("Writing symmetry graph raw image..")
        graph.write_matrix_image_raw(hide_equal_predicates=True)
        
    automorphisms = graph.find_automorphisms(time_limit)
    graph.write_or_print_automorphisms(automorphisms, hide_equal_predicates=True, write=False, dump=False)
    sys.stdout.flush()

