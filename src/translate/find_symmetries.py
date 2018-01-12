#! /usr/bin/env python

import normalize
import options
import pddl_parser
from symmetries_module import SymmetryGraph
import sys
import timers


if __name__ == "__main__":
    timer = timers.Timer()

    only_object_symmetries = options.only_object_symmetries
    stabilize_initial_state = not options.do_not_stabilize_initial_state
    stabilize_goal = not options.do_not_stabilize_goal
    time_limit = options.bliss_time_limit

    use_bolding = options.bolding_abstract_structure_image 
    write_original_size = options.write_abstract_structure_image_original_size
    abstract_structure_image_target_size = options.abstract_structure_image_target_size

    with timers.timing("Parsing pddl..", True):    
        task = pddl_parser.open()
    with timers.timing("Normalizing task..", True):    
        normalize.normalize(task)
    #print("Dumping task..")
    #task.dump()
    with timers.timing("Creating symmetry graph..", True):    
        graph = SymmetryGraph(task, only_object_symmetries, stabilize_initial_state, stabilize_goal)
    if options.add_mutex_groups:
        print("cannot add mutex groups -- translator is not run!")
        exit(1)
    if options.dump_dot_graph:
        f = open('out.dot', 'w')
        graph.write_dot_graph(f, hide_equal_predicates=True)
        f.close()
    if options.write_abstract_structure_image_raw:
        with timers.timing("Writing symmetry graph raw image..", True):    
            graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=1, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size)
    if options.write_abstract_structure_image_reg:
        with timers.timing("Writing symmetry graph grayscale 8bit image..", True):    
            graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=3, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size)
    if options.write_abstract_structure_image_int:
        with timers.timing("Writing symmetry graph grayscale 32bit image..", True):    
            graph.write_matrix_image_grayscale(hide_equal_predicates=True, shrink_ratio=6, bolded=use_bolding, target_size=abstract_structure_image_target_size, write_original_size=write_original_size)
        
    if not options.do_not_find_automorphisms:
        automorphisms = graph.find_automorphisms(time_limit)
        graph.write_or_print_automorphisms(automorphisms, hide_equal_predicates=True, write=False, dump=False)
    
    print("Done! %s" % timer)

    sys.stdout.flush()

