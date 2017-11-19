#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import numpy
import os

from collections import defaultdict

from downward.experiment import FastDownwardExperiment
from downward.reports.absolute import AbsoluteReport
from downward.reports.scatter import ScatterPlotReport

from lab.reports import Attribute, geometric_mean

exp = FastDownwardExperiment()

REVISION = 'cb5995d31cca'

def rename_revision(run):
    algo = run['algorithm']
    algo = algo.replace('{}-'.format(REVISION), '')
    run['algorithm'] = algo
    return run

exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-grounding-regular-and-reduced-eval'),filter=[rename_revision])
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-grounding-regular-and-reduced-nogoal-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-grounding-regular-and-reduced-learning-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-grounding-regular-and-reduced-learning-nogoal-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-h2mutexes-regular-and-reduced-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-h2mutexes-regular-and-reduced-nogoal-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-h2mutexes-regular-and-reduced-learning-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-18-h2mutexes-regular-and-reduced-learning-nogoal-eval'),filter=[rename_revision],merge=True)

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
attributes.append('translator_time_instantiating')
attributes.append('translator_time_completing_instantiation')

exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=[
    'translate',
    'translate-reduced-grounding',
    'translate-reduced-grounding-nogoal',
]),name='grounding',outfile=os.path.join(exp.eval_dir, 'grounding.html'))

exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=[
    'translate-h2mutexes',
    'translate-reduced-h2mutexes',
    'translate-reduced-h2mutexes-nogoal',
]),name='h2mutexes',outfile=os.path.join(exp.eval_dir, 'h2mutexes.html'))

def large_diff_translator_time_instantiating(run1, run2):
    if abs(run1.get('translator_time_instantiating', float('inf')) - run2.get('translator_time_instantiating', float('inf'))) < 10:
        return None
    return run1['domain']

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding-nogoal',
        ],
        attributes=['translator_time_instantiating'],
        #get_category=large_diff_translator_time_instantiating,
        format='tex',
    ),
    name='grounding-nogoal-scatter',
    outfile=os.path.join(exp.eval_dir, 'grounding-nogoal-scatter')
)

def large_diff_translator_time_computing_h2_mutex_groups(run1, run2):
    if abs(run1.get('translator_time_computing_h2_mutex_groups', float('inf')) - run2.get('translator_time_computing_h2_mutex_groups', float('inf'))) < 10:
        return None
    return run1['domain']

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes-nogoal',
        ],
        attributes=['translator_time_computing_h2_mutex_groups'],
        #get_category=large_diff_translator_time_computing_h2_mutex_groups,
        format='tex',
    ),
    name='h2mutexes-nogoal-scatter',
    outfile=os.path.join(exp.eval_dir, 'h2mutexes-nogoal-scatter')
)

exp.run_steps()
