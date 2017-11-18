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
    benchmarks_dir=os.path.expanduser('~/repos/downward/benchmarks')
    # optimal union satisficing
    suite = [
    'openstacks-sat08-adl', 'miconic-simpleadl', 'barman-sat14-strips',
    'transport-opt11-strips', 'openstacks-sat08-strips', 'logistics98',
    'parking-sat11-strips', 'psr-large', 'rovers', 'floortile-opt14-strips',
    'barman-opt14-strips', 'zenotravel', 'elevators-sat11-strips',
    'nomystery-opt11-strips', 'parcprinter-08-strips', 'tidybot-opt11-strips',
    'cavediving-14-adl', 'pegsol-opt11-strips', 'maintenance-opt14-adl',
    'citycar-opt14-adl', 'pipesworld-notankage', 'woodworking-sat08-strips',
    'woodworking-opt11-strips', 'driverlog', 'gripper', 'visitall-sat11-strips',
    'openstacks', 'hiking-opt14-strips', 'sokoban-opt11-strips',
    'tetris-sat14-strips', 'parcprinter-opt11-strips', 'openstacks-strips',
    'parcprinter-sat11-strips', 'grid', 'sokoban-opt08-strips',
    'elevators-opt08-strips', 'openstacks-sat14-strips', 'barman-sat11-strips',
    'tidybot-sat11-strips', 'mystery', 'visitall-opt14-strips',
    'childsnack-sat14-strips', 'sokoban-sat11-strips', 'trucks',
    'sokoban-sat08-strips', 'barman-opt11-strips', 'childsnack-opt14-strips',
    'parking-opt14-strips', 'openstacks-opt11-strips', 'elevators-sat08-strips',
    'movie', 'tidybot-opt14-strips', 'freecell', 'openstacks-opt14-strips',
    'scanalyzer-sat11-strips', 'ged-opt14-strips', 'pegsol-sat11-strips',
    'transport-opt08-strips', 'mprime', 'floortile-opt11-strips',
    'transport-sat08-strips', 'pegsol-08-strips', 'blocks',
    'floortile-sat11-strips', 'thoughtful-sat14-strips', 'openstacks-opt08-strips',
    'visitall-sat14-strips', 'pipesworld-tankage', 'scanalyzer-opt11-strips',
    'storage', 'maintenance-sat14-adl', 'optical-telegraphs',
    'elevators-opt11-strips', 'miconic', 'logistics00', 'depot',
    'transport-sat11-strips', 'openstacks-opt08-adl', 'psr-small', 'satellite',
    'assembly', 'citycar-sat14-adl', 'schedule', 'miconic-fulladl',
    'pathways-noneg', 'tetris-opt14-strips', 'ged-sat14-strips', 'pathways',
    'woodworking-opt08-strips', 'floortile-sat14-strips', 'nomystery-sat11-strips',
    'transport-opt14-strips', 'woodworking-sat11-strips', 'philosophers',
    'trucks-strips', 'hiking-sat14-strips', 'transport-sat14-strips',
    'openstacks-sat11-strips', 'scanalyzer-08-strips', 'visitall-opt11-strips',
    'psr-middle', 'airport', 'parking-opt11-strips', 'tpp', 'parking-sat14-strips']
    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    if is_test_run():
        suite = ['gripper:prob01.pddl','gripper:prob02.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('translate', [], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3G']),
        IssueConfig('translate-reduced-grounding', ['--translate-options', '--compute-symmetries', '--only-object-symmetries', '--compute-symmetric-object-sets', '--symmetry-reduced-grounding', '--expand-reduced-task', '--bliss-time-limit', '300', ], driver_options=['--translate', '--translate-time-limit', '30m', '--translate-memory-limit', '3G']),
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
        '{}-translate'.format(REVISION),
        '{}-translate-reduced-grounding'.format(REVISION),
    ],filter=[compute_removed_count_in_each_step])

    exp.add_scatter_plot_report(
        algo_pair=[
            '{}-translate'.format(REVISION),
            '{}-translate-reduced-grounding'.format(REVISION),
        ],
        attribute='translator_time_instantiating',
    )

    exp.run_steps()

main(revisions=[REVISION])
