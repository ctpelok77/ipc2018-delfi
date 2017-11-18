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
    suite = ['elevators', 'floortile', 'nomystery', 'parking', 'spanner',
    'transport']
    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    if is_test_run():
        suite = ['elevators:p24_40_1.pddl', 'floortile:p4-3-2.pddl',
        'nomystery:p-c10-08.pddl', 'parking:p28-15.pddl',
        'spanner:prob-130-130-80-1396209574.pddl', 'transport:p-2-50-20.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate-h2mutexes', ['--translate-options', '--h2-mutexes', '--only-positive-literals'], driver_options=['--translate', '--translate-time-limit', '1m', '--translate-memory-limit', '3G']),
        IssueConfig('translate-reduced-h2mutexes', ['--translate-options', '--compute-symmetries', '--bliss-time-limit', '300', '--only-object-symmetries', '--compute-symmetric-object-sets', '--symmetry-reduced-grounding-for-h2-mutexes', '--expand-reduced-h2-mutexes', '--h2-mutexes', '--only-positive-literals'], driver_options=['--translate', '--translate-time-limit', '1m', '--translate-memory-limit', '3G']),
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
    time_h2mutexes_program = Attribute('time_h2mutexes_program', absolute=True, min_wins=True)
    time_h2mutexes_model = Attribute('time_h2mutexes_model', absolute=True, min_wins=True)
    time_h2mutexes_expand = Attribute('time_h2mutexes_expand', absolute=True, min_wins=True)
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
        time_h2mutexes_program,
        time_h2mutexes_model,
        time_h2mutexes_expand,
        bliss_out_of_memory,
        bliss_out_of_time,
        num_transpositions,
        num_used_symmetric_object_sets,
        performed_reduction,
    ]
    attributes = ['error', 'run_dir'] # exp.DEFAULT_TABLE_ATTRIBUTES
    attributes.extend(extra_attributes)
    attributes.append('translator_time_symmetries0_computing_symmetries')
    attributes.append('translator_time_computing_h2_mutex_groups')

    exp.add_fetcher(name='parse-memory-error', parsers=['translator-memory-error-parser.py'])

    def compute_removed_count_in_each_step(props):
        count_lifted = props.get('generator_count_lifted', 0)
        count_grounded_1 = props.get('generator_count_grounded_1_after_grounding', 0)
        count_grounded_2 = props.get('generator_count_grounded_2_after_sas_task', 0)
        count_grounded_3 = props.get('generator_count_grounded_3_after_filtering_props', 0)
        count_grounded_4 = props.get('generator_count_grounded_4_after_reordering_filtering_vars', 0)
        props['removed1_after_grounding'] = count_lifted - count_grounded_1
        props['removed2_after_sas_task'] = count_grounded_1 - count_grounded_2
        props['removed3_after_filtering_props'] = count_grounded_2 - count_grounded_3
        props['removed4_after_reordering_filtering_vars'] = count_grounded_3 - count_grounded_4
        return props

    exp.add_absolute_report_step(attributes=attributes,filter_algorithm=[
        '{}-translate-h2mutexes'.format(REVISION),
        '{}-translate-reduced-h2mutexes'.format(REVISION),
    ],filter=[compute_removed_count_in_each_step])

    exp.add_scatter_plot_report(
        algo_pair=[
            '{}-translate-h2mutexes'.format(REVISION),
            '{}-translate-reduced-h2mutexes'.format(REVISION),
        ],
        attribute='translator_time_computing_h2_mutex_groups',
    )

    exp.run_steps()

main(revisions=[REVISION])
