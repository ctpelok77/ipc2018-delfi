#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from lab.reports import Attribute, geometric_mean

from common_setup import IssueConfig, IssueExperiment, DEFAULT_OPTIMAL_SUITE, is_test_run
try:
    from relativescatter import RelativeScatterPlotReport
    matplotlib = True
except ImportError:
    print 'matplotlib not availabe, scatter plots not available'
    matplotlib = False

REVISION = 'cb5995d31cca'

def main(revisions=None):
    benchmarks_dir=os.path.expanduser('~/repos/downward/learning-benchmarks')
    # learning
    suite = ['learning-elevators', 'learning-floortile', 'learning-nomystery',
    'learning-parking', 'learning-spanner', 'learning-transport']
    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    if is_test_run():
        suite = ['learning-elevators:p24_40_1.pddl',
        'learning-floortile:p4-3-2.pddl',
        'learning-nomystery:p-c10-08.pddl', 'learning-parking:p28-15.pddl',
        'learning-spanner:prob-130-130-80-1396209574.pddl',
        'learning-transport:p-2-50-20.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        #IssueConfig('translate', [], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3G']),
        IssueConfig('translate-reduced-grounding-nogoal', ['--translate-options', '--compute-symmetries', '--do-not-stabilize-goal', '--only-object-symmetries', '--compute-symmetric-object-sets', '--symmetry-reduced-grounding', '--expand-reduced-task', '--bliss-time-limit', '300', ], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3G']),
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)
    exp.add_resource('symmetries_parser', 'symmetries-parser.py', dest='symmetries-parser.py')
    exp.add_command('symmetries-parser', ['{symmetries_parser}'])
    del exp.commands['parse-search']
    del exp.commands['compress-output-sas']

    generator_count_lifted = Attribute('generator_count_lifted', absolute=True, min_wins=False)
    generator_orders_lifted = Attribute('generator_orders_lifted', absolute=True)
    generator_orders_lifted_list = Attribute('generator_orders_lifted_list', absolute=True)
    generator_order_lifted_2 = Attribute('generator_order_lifted_2', absolute=True, min_wins=False)
    generator_order_lifted_3 = Attribute('generator_order_lifted_3', absolute=True, min_wins=False)
    generator_order_lifted_4 = Attribute('generator_order_lifted_4', absolute=True, min_wins=False)
    generator_order_lifted_5 = Attribute('generator_order_lifted_5', absolute=True, min_wins=False)
    generator_order_lifted_6 = Attribute('generator_order_lifted_6', absolute=True, min_wins=False)
    generator_order_lifted_7 = Attribute('generator_order_lifted_7', absolute=True, min_wins=False)
    generator_order_lifted_8 = Attribute('generator_order_lifted_8', absolute=True, min_wins=False)
    generator_order_lifted_9 = Attribute('generator_order_lifted_9', absolute=True, min_wins=False)
    generator_order_lifted_max = Attribute('generator_order_lifted_max', absolute=True, min_wins=False)
    time_symmetries1_symmetry_graph = Attribute('time_symmetries1_symmetry_graph', absolute=True, min_wins=True)
    time_symmetries2_bliss = Attribute('time_symmetries2_bliss', absolute=True, min_wins=True)
    time_symmetries3_translate_automorphisms = Attribute('time_symmetries3_translate_automorphisms', absolute=True, min_wins=True)
    time_bounds_and_subsets = Attribute('time_bounds_and_subsets', absolute=True, min_wins=True)
    time_grounding_program = Attribute('time_grounding_program', absolute=True, min_wins=True)
    time_grounding_model = Attribute('time_grounding_model', absolute=True, min_wins=True)
    time_grounding_expand = Attribute('time_grounding_expand', absolute=True, min_wins=True)
    bliss_out_of_memory = Attribute('bliss_out_of_memory', absolute=True, min_wins=True)
    bliss_out_of_time = Attribute('bliss_out_of_time', absolute=True, min_wins=True)
    num_transpositions = Attribute('num_transpositions', absolute=True, min_wins=False)
    num_used_symmetric_object_sets = Attribute('num_used_symmetric_object_sets', absolute=True, min_wins=False)
    performed_reduction = Attribute('performed_reduction', absolute=True, min_wins=False)


    extra_attributes = [
        generator_count_lifted,
        generator_orders_lifted,
        generator_orders_lifted_list,
        generator_order_lifted_2,
        generator_order_lifted_3,
        generator_order_lifted_4,
        generator_order_lifted_5,
        generator_order_lifted_6,
        generator_order_lifted_7,
        generator_order_lifted_8,
        generator_order_lifted_9,
        generator_order_lifted_max,
        time_symmetries1_symmetry_graph,
        time_symmetries2_bliss,
        time_symmetries3_translate_automorphisms,
        time_bounds_and_subsets,
        time_grounding_program,
        time_grounding_model,
        time_grounding_expand,
        bliss_out_of_memory,
        bliss_out_of_time,
        num_transpositions,
        num_used_symmetric_object_sets,
        performed_reduction,
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_time_symmetries0_computing_symmetries')
    attributes.append('translator_time_instantiating')

    exp.add_fetcher(name='parse-memory-error', parsers=['translator-memory-error-parser.py'])

    exp.add_absolute_report_step(attributes=attributes,filter_algorithm=[
        #'{}-translate'.format(REVISION),
        '{}-translate-reduced-grounding-nogoal'.format(REVISION),
    ])

    exp.run_steps()

main(revisions=[REVISION])
