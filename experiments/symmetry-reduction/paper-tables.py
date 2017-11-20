#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import numpy
import os

from collections import defaultdict

from downward.experiment import FastDownwardExperiment
from downward.reports import PlanningReport
from downward.reports.absolute import AbsoluteReport
from downward.reports.scatter import ScatterPlotReport

from lab.reports import Attribute, geometric_mean

exp = FastDownwardExperiment()

REVISION = '818d58790dc5'

def rename_revision(run):
    algo = run['algorithm']
    algo = algo.replace('{}-'.format(REVISION), '')
    run['algorithm'] = algo
    return run

exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-19-grounding-regular-and-reduced-eval'),filter=[rename_revision])
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-19-grounding-reduced-noexpand-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-19-h2mutexes-regular-and-reduced-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-19-h2mutexes-reduced-noexpand-eval'),filter=[rename_revision],merge=True)

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

################### reports to generate lists of doains #####################

class DomainsWithLargeDifferencesReport(PlanningReport):
    def __init__(self, attribute_threshold_pairs, **kwargs):
        self.attribute_threshold_pairs = attribute_threshold_pairs
        kwargs.setdefault('format', 'txt')
        PlanningReport.__init__(self, **kwargs)

    def get_text(self):
        """
        We do not need any markup processing or loop over attributes here,
        so the get_text() method is implemented right here.
        """
        attributes = set()
        for attribute, threshold in self.attribute_threshold_pairs:
            attributes.add(attribute)

        domain_problem_algorithm_attribute_values = {}
        algo_domain_problem_algorithm = {}
        for algo in self.algorithms:
            algo_domain_problem_algorithm[algo] = {}
            for domain in self.domains.keys():
                algo_domain_problem_algorithm[algo][domain] = defaultdict(dict)
        for (domain, algo), runs in self.domain_algorithm_runs.items():
            for attribute in attributes:
                for run in runs:
                    problem = run['problem']
                    #value = run.get(attribute, float('inf'))
                    value = run.get(attribute, None)
                    algo_domain_problem_algorithm[algo][domain][problem][attribute] = value

        assert(len(self.algorithms) == 2)
        algo1 = self.algorithms[0]
        algo2 = self.algorithms[1]
        attribute_to_domains_with_large_diff = defaultdict(set)
        for domain, problems in self.domains.items():
            for problem in problems:
                for attribute, threshold in self.attribute_threshold_pairs:
                    val1 = algo_domain_problem_algorithm[algo1][domain][problem][attribute]
                    val2 = algo_domain_problem_algorithm[algo2][domain][problem][attribute]
                    if val1 is not None and val2 is not None and abs(val1 - val2) > threshold:
                        attribute_to_domains_with_large_diff[attribute].add(domain)

        lines = []
        for attribute in attributes:
            lines.append("{}:".format(attribute))
            lines.append("[")
            for domain in attribute_to_domains_with_large_diff[attribute]:
                lines.append("  '{}',".format(domain))
            lines.append("]")
            lines.append("")
        return '\n'.join(lines)

exp.add_report(
    DomainsWithLargeDifferencesReport(
        [('translator_time_instantiating', 3)],
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding--noexpandnogoal',
        ],
    ),
    name='domains-with-large-differences-time-grounding',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-grounding'),
)

exp.add_report(
    DomainsWithLargeDifferencesReport(
        [('translator_time_computing_h2_mutex_groups', 120)],
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes--noexpand-nogoal',
        ],
    ),
    name='domains-with-large-differences-time-mutexes',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-mutexes'),
)

################### regular reports ########################################

exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=[
    'translate',
    'translate-reduced-grounding',
    'translate-reduced-grounding-noexpand',
    'translate-reduced-grounding-nogoal',
    'translate-reduced-grounding--noexpandnogoal',
]),name='grounding',outfile=os.path.join(exp.eval_dir, '2017-11-19-grounding.html'))

exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=[
    'translate-h2mutexes',
    'translate-reduced-h2mutexes',
    'translate-reduced-h2mutexes-noexpand',
    'translate-reduced-h2mutexes-nogoal',
    'translate-reduced-h2mutexes--noexpand-nogoal',
]),name='h2mutexes',outfile=os.path.join(exp.eval_dir, '2017-11-19-h2mutexes.html'))

################### scatter plots ########################################

# generated with above DomainsWithLargeDifferencesReport
domains_with_diff_of_translator_time_instantiating_larger_3 = [
  'satellite',
  'pipesworld-tankage',
  'trucks',
  'openstacks-strips',
  'logistics98',
  'learning-elevators',
  'tpp',
  'psr-large',
  'learning-spanner',
]

def large_diff_translator_time_instantiating(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_instantiating_larger_3:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding-nogoal',
        ],
        attributes=['translator_time_instantiating'],
        get_category=large_diff_translator_time_instantiating,
        format='tex',
    ),
    name='scatter-grounding-time-regular-vs-reducedandexpand',
    outfile=os.path.join(exp.eval_dir, 'scatter-grounding-time-regular-vs-reducedandexpand')
)

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding--noexpandnogoal',
        ],
        attributes=['translator_time_instantiating'],
        get_category=large_diff_translator_time_instantiating,
        format='tex',
    ),
    name='scatter-grounding-time-regular-vs-reduced',
    outfile=os.path.join(exp.eval_dir, 'scatter-grounding-time-regular-vs-reduced')
)

# generated with above DomainsWithLargeDifferencesReport, ignoring those cases
# where one algo did not finish the computation.
domains_with_diff_of_translator_time_computing_h2_mutex_groups_larger_120 = [
  'woodworking-sat08-strips',
  'satellite',
  'parcprinter-sat11-strips',
  'trucks',
  'childsnack-opt14-strips',
  'barman-sat11-strips',
  'barman-sat14-strips',
  'parcprinter-08-strips',
  'childsnack-sat14-strips',
  'logistics98',
  'woodworking-opt08-strips',
  'nomystery-sat11-strips',
]

def large_diff_translator_time_computing_h2_mutex_groups(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_computing_h2_mutex_groups_larger_120:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes-nogoal',
        ],
        attributes=['translator_time_computing_h2_mutex_groups'],
        get_category=large_diff_translator_time_computing_h2_mutex_groups,
        format='tex',
    ),
    name='scatter-h2mutexes-time-regular-vs-reducedandexpand',
    outfile=os.path.join(exp.eval_dir, 'scatter-h2mutexes-time-regular-vs-reducedandexpand')
)

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes--noexpand-nogoal',
        ],
        attributes=['translator_time_computing_h2_mutex_groups'],
        get_category=large_diff_translator_time_computing_h2_mutex_groups,
        format='tex',
    ),
    name='scatter-h2mutexes-time-regular-vs-reduced',
    outfile=os.path.join(exp.eval_dir, 'scatter-h2mutexes-time-regular-vs-reduced')
)

exp.run_steps()
