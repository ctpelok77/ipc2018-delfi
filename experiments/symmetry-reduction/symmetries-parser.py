#! /usr/bin/env python

import re

from lab.parser import Parser

parser = Parser()
parser.add_pattern('generator_count_lifted', 'Number of lifted generators: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_2', 'Lifted generator order 2: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_3', 'Lifted generator order 3: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_4', 'Lifted generator order 4: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_5', 'Lifted generator order 5: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_6', 'Lifted generator order 6: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_7', 'Lifted generator order 7: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_8', 'Lifted generator order 8: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_9', 'Lifted generator order 9: (\d+)', required=False, type=int)
parser.add_pattern('generator_order_lifted_max', 'Maximum generator order: (\d+)', required=False, type=int)
parser.add_pattern('num_transpositions', 'Number of transpositions: (\d+)', required=False, type=int)
#parser.add_pattern('size_largest_symmetric_object_set', 'Size of largest symmetric object set: (\d+)', required=False, type=int)
#parser.add_pattern('max_predicate_arity_simple', 'Maximum predicate arity simple: (\d+)', required=False, type=int)
#parser.add_pattern('max_operator_arity_simple', 'Maximum operator arity given largest symmetric object set simple: (\d+)', required=False, type=int)
#parser.add_pattern('max_axiom_arity_simple', 'Maximum axiom arity given largest symmetric object set simple: (\d+)', required=False, type=int)
#parser.add_pattern('max_predicate_arity_tight', 'Maximum predicate arity given largest symmetric object set tight: (\d+)', required=False, type=int)
#parser.add_pattern('max_operator_arity_tight', 'Maximum operator arity given largest symmetric object set tight: (\d+)', required=False, type=int)
#parser.add_pattern('max_axiom_arity_tight', 'Maximum axiom arity given largest symmetric object set tight: (\d+)', required=False, type=int)
parser.add_pattern('num_used_symmetric_object_sets', 'Number of symmetric object sets used for symmetry reduction: (\d+)', required=False, type=int)
parser.add_pattern('num_reachable_pairs', 'Found (\d+) reachable pairs of literals', required=False, type=int)
parser.add_pattern('num_unreachable_pairs', 'Found (\d+) unreachable pairs of literals', required=False, type=int)
parser.add_pattern('num_expanded_unreachable_pairs', 'Expanded h2 mutex pairs to (\d+)', required=False, type=int)
parser.add_pattern('time_symmetries1_symmetry_graph', 'Done creating symmetry graph: (.+)s', required=False, type=float)
parser.add_pattern('time_symmetries2_bliss', 'Done searching for automorphisms: (.+)s', required=False, type=float)
parser.add_pattern('time_symmetries3_translate_automorphisms', 'Done translating automorphisms: (.+)s', required=False, type=float)
parser.add_pattern('time_symmetric_object_sets', 'Time to compute symmetric object sets: (.+)s', required=False, type=float)
parser.add_pattern('time_bounds_and_subsets', 'Total time to compute bounds and determine subsets of symmetric object sets: (.+)s', required=False, type=float)
parser.add_pattern('time_grounding_program', 'Time to generate prolog program: (.+)s', required=False, type=float)
parser.add_pattern('time_grounding_model', 'Time to compute model of prolog program: (.+)s', required=False, type=float)
parser.add_pattern('time_grounding_expand', 'Time to expand reduced model: (.+)s', required=False, type=float)
parser.add_pattern('time_h2mutexes_program', 'Time to compute h2 mutexes reachability program: (.+)s', required=False, type=float)
parser.add_pattern('time_h2mutexes_model', 'Time to compute model of reachability program: (.+)s', required=False, type=float)
parser.add_pattern('time_h2mutexes_expand', 'Time to expand h2 mutexes: (.+)s', required=False, type=float)


def parse_generator_orders(content, props):
    lifted_generator_orders = re.findall(r'Lifted generator orders: \[(.*)\]', content)
    props['generator_orders_lifted'] = lifted_generator_orders
    lifted_generator_orders_list = re.findall(r'Lifted generator orders list: \[(.*)\]', content)
    props['generator_orders_lifted_list'] = lifted_generator_orders_list
    grounded_generator_orders = re.findall(r'Grounded generator orders: \[(.*)\]', content)
    props['generator_orders_grounded'] = grounded_generator_orders
    grounded_generator_orders_list = re.findall(r'Grounded generator orders list: \[(.*)\]', content)
    props['generator_orders_grounded_list'] = grounded_generator_orders_list

parser.add_function(parse_generator_orders)

def parse_boolean_flags(content, props):
    bliss_memory_out = False
    bliss_timeout = False
    generator_lifted_affecting_actions_axioms = False
    generator_lifted_mapping_actions_axioms = False
    generator_not_well_defined_for_search = False
    ignore_none_of_those_mapping = False
    simplify_var_removed = False
    simplify_val_removed = False
    reorder_var_removed = False
    reduction = False
    lines = content.split('\n')
    for line in lines:
        if 'Bliss memory out' in line:
            bliss_memory_out = True

        if 'Bliss timeout' in line:
            bliss_timeout = True

        if line == 'Actually can perform a symmetry reduction':
            reduction = True

    props['bliss_out_of_memory'] = bliss_memory_out
    props['bliss_out_of_time'] = bliss_timeout
    props['performed_reduction'] = reduction

parser.add_function(parse_boolean_flags)

#def parse_symmetry_reduction_potential(content, props):
    #size_largest_symmetric_object_set = props.get('size_largest_symmetric_object_set', 0)
    #max_predicate_arity_simple = props.get('max_predicate_arity_simple', 0)
    #max_operator_arity_simple = props.get('max_operator_arity_simple', 0)
    #max_axiom_arity_simple = props.get('max_axiom_arity_simple', 0)
    #has_symmetry_reduction_potential_simple = size_largest_symmetric_object_set > max(max_predicate_arity_simple, max_operator_arity_simple, max_axiom_arity_simple)
    #props['has_symmetry_reduction_potential_simple'] = has_symmetry_reduction_potential_simple
    #max_predicate_arity_tight = props.get('max_predicate_arity_tight', 0)
    #max_operator_arity_tight = props.get('max_operator_arity_tight', 0)
    #max_axiom_arity_tight = props.get('max_axiom_arity_tight', 0)
    #has_symmetry_reduction_potential_tight = size_largest_symmetric_object_set > max(max_predicate_arity_tight, max_operator_arity_tight, max_axiom_arity_tight)
    #props['has_symmetry_reduction_potential_tight'] = has_symmetry_reduction_potential_tight

#parser.add_function(parse_symmetry_reduction_potential)

parser.parse()
