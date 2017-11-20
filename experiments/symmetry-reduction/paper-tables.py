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

REVISION = '212720d86b23'

def rename_revision(run):
    algo = run['algorithm']
    algo = algo.replace('{}-'.format(REVISION), '')
    run['algorithm'] = algo
    return run

exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-20-grounding-eval'),filter=[rename_revision])
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-20-h2mutexesrelaxed-eval'),filter=[rename_revision],merge=True)
exp.add_fetcher(os.path.expanduser('~/repos/downward/symmetry-reduction/experiments/symmetry-reduction/data/2017-11-20-h2mutexes-eval'),filter=[rename_revision],merge=True)

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
num_reachable_pairs = Attribute('num_reachable_pairs', absolute=True, min_wins=False)
num_unreachable_pairs = Attribute('num_unreachable_pairs', absolute=True, min_wins=False)
num_expanded_unreachable_pairs = Attribute('num_expanded_unreachable_pairs', absolute=True, min_wins=False)
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
    num_reachable_pairs,
    num_unreachable_pairs,
    num_expanded_unreachable_pairs,
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
                    if val1 is not None and val2 is not None and (val1 >= threshold * val2 or val2 >= threshold * val1):
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
        [('translator_time_instantiating', 10)],
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding-nogoal',
        ],
    ),
    name='domains-with-large-differences-time-grounding-reduced',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-grounding-reduced'),
)

exp.add_report(
    DomainsWithLargeDifferencesReport(
        [('translator_time_instantiating', 10)],
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding-expand-nogoal',
        ],
    ),
    name='domains-with-large-differences-time-grounding-reducedexpand',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-grounding-reducedexpand'),
)

exp.add_report(
    DomainsWithLargeDifferencesReport(
        [('translator_time_computing_h2_mutex_groups', 10)],
        filter_algorithm=[
            'translate-h2mutexesrelaxed',
            'translate-reduced-h2mutexesrelaxed-nogoal',
        ],
    ),
    name='domains-with-large-differences-time-mutexesrelaxed-reduced',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-mutexesrelaxed-reduced'),
)

exp.add_report(
    DomainsWithLargeDifferencesReport(
        [('translator_time_computing_h2_mutex_groups', 10)],
        filter_algorithm=[
            'translate-h2mutexesrelaxed',
            'translate-reduced-h2mutexesrelaxed-expand-nogoal',
        ],
    ),
    name='domains-with-large-differences-time-mutexesrelaxed-reducedexpand',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-mutexesrelaxed-reducedexpand'),
)

exp.add_report(
    DomainsWithLargeDifferencesReport(
        [('translator_time_computing_h2_mutex_groups', 10)],
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes-nogoal',
        ],
    ),
    name='domains-with-large-differences-time-mutexes-reduced',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-mutexes-reduced'),
)

exp.add_report(
    DomainsWithLargeDifferencesReport(
        [('translator_time_computing_h2_mutex_groups', 10)],
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes-expand-nogoal',
        ],
    ),
    name='domains-with-large-differences-time-mutexes-reducedexpand',
    outfile=os.path.join(exp.eval_dir, 'domains-with-large-differences-time-mutexes-reducedexpand'),
)

################### regular reports ########################################

exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=[
    'translate',
    'translate-reduced-grounding-nogoal',
    'translate-reduced-grounding-expand-nogoal',
]),name='grounding',outfile=os.path.join(exp.eval_dir, '2017-11-20-grounding.html'))

exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=[
    'translate-h2mutexesrelaxed',
    'translate-reduced-h2mutexesrelaxed-nogoal',
    'translate-reduced-h2mutexesrelaxed-expand-nogoal',
]),name='h2mutexes',outfile=os.path.join(exp.eval_dir, '2017-11-20-h2mutexesrelaxed.html'))

exp.add_report(AbsoluteReport(attributes=attributes,filter_algorithm=[
    'translate-h2mutexes',
    'translate-reduced-h2mutexes-nogoal',
    'translate-reduced-h2mutexes-expand-nogoal',
]),name='h2mutexes',outfile=os.path.join(exp.eval_dir, '2017-11-20-h2mutexes.html'))

################### scatter plots ########################################

### grounding ###

# generated with above DomainsWithLargeDifferencesReport, ignoring those cases
# where one algo did not finish the computation.
domains_with_diff_of_translator_time_instantiating_for_grounding_reduced_larger_10 = [
  'psr-small',
  'satellite',
  'childsnack-sat14-strips',
  'blocks',
  'gripper',
  'miconic-simpleadl',
  'visitall-opt11-strips',
  'childsnack-opt14-strips',
  'miconic',
  'learning-spanner',
]

def domain_category_for_grounding_reduced(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_instantiating_for_grounding_reduced_larger_10:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding-nogoal',
        ],
        attributes=['translator_time_instantiating'],
        get_category=domain_category_for_grounding_reduced,
        format='tex',
    ),
    name='scatter-grounding-time-regular-vs-reduced',
    outfile=os.path.join(exp.eval_dir, 'scatter-grounding-time-regular-vs-reduced')
)

# generated with above DomainsWithLargeDifferencesReport, ignoring those cases
# where one algo did not finish the computation.
domains_with_diff_of_translator_time_instantiating_for_grounding_reducedexpand_larger_10 = [
  'psr-small',
  'satellite',
  'blocks',
  'miconic-simpleadl',
  'visitall-opt11-strips',
  'miconic',
  'learning-spanner',
]

def domain_category_for_grounding_reducedexpand(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_instantiating_for_grounding_reducedexpand_larger_10:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate',
            'translate-reduced-grounding-expand-nogoal',
        ],
        attributes=['translator_time_instantiating'],
        get_category=domain_category_for_grounding_reducedexpand,
        format='tex',
    ),
    name='scatter-grounding-time-regular-vs-reducedandexpand',
    outfile=os.path.join(exp.eval_dir, 'scatter-grounding-time-regular-vs-reducedandexpand')
)

### mutexesrelaxed ###

# generated with above DomainsWithLargeDifferencesReport, ignoring those cases
# where one algo did not finish the computation.
domains_with_diff_of_translator_time_instantiating_for_mutexesrelaxed_reduced_larger_10 = [
  'satellite',
  'childsnack-sat14-strips',
  'gripper',
  'miconic-simpleadl',
  'movie',
  'miconic-fulladl',
  'visitall-opt11-strips',
  'barman-sat11-strips',
  'barman-sat14-strips',
  'childsnack-opt14-strips',
  'tpp',
  'miconic',
]

def domain_category_for_mutexesrelaxed_reduced(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_instantiating_for_mutexesrelaxed_reduced_larger_10:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate-h2mutexesrelaxed',
            'translate-reduced-h2mutexesrelaxed-nogoal',
        ],
        attributes=['translator_time_computing_h2_mutex_groups'],
        get_category=domain_category_for_mutexesrelaxed_reduced,
        format='tex',
    ),
    name='scatter-h2mutexesrelaxed-time-regular-vs-reduced',
    outfile=os.path.join(exp.eval_dir, 'scatter-h2mutexesrelaxed-time-regular-vs-reduced')
)

# generated with above DomainsWithLargeDifferencesReport, ignoring those cases
# where one algo did not finish the computation.
domains_with_diff_of_translator_time_instantiating_for_mutexesrelaxed_reducedexpand_larger_10 = [
  'satellite',
  'childsnack-sat14-strips',
  'gripper',
  'miconic-simpleadl',
  'movie',
  'miconic-fulladl',
  'visitall-opt11-strips',
  'barman-sat11-strips',
  'barman-sat14-strips',
  'childsnack-opt14-strips',
  'tpp',
  'miconic',
]

def domain_category_for_mutexesrelaxed_reducedexpand(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_instantiating_for_mutexesrelaxed_reducedexpand_larger_10:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate-h2mutexesrelaxed',
            'translate-reduced-h2mutexesrelaxed-expand-nogoal',
        ],
        attributes=['translator_time_computing_h2_mutex_groups'],
        get_category=domain_category_for_mutexesrelaxed_reducedexpand,
        format='tex',
    ),
    name='scatter-h2mutexesrelaxed-time-regular-vs-reducedandexpand',
    outfile=os.path.join(exp.eval_dir, 'scatter-h2mutexesrelaxed-time-regular-vs-reducedandexpand')
)

### mutexes ###

# generated with above DomainsWithLargeDifferencesReport, ignoring those cases
# where one algo did not finish the computation.
domains_with_diff_of_translator_time_instantiating_for_mutexes_reducedexpand_larger_10 = [

]

def domain_category_for_mutexes_reduced(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_instantiating_for_mutexes_reduced_larger_10:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes-nogoal',
        ],
        attributes=['translator_time_computing_h2_mutex_groups'],
        get_category=domain_category_for_mutexes_reduced,
        format='tex',
    ),
    name='scatter-h2mutexes-time-regular-vs-reduced',
    outfile=os.path.join(exp.eval_dir, 'scatter-h2mutexes-time-regular-vs-reduced')
)

# generated with above DomainsWithLargeDifferencesReport, ignoring those cases
# where one algo did not finish the computation.
domains_with_diff_of_translator_time_instantiating_for_mutexes_reducedexpand_larger_10 = [

]

def domain_category_for_mutexes_reducedexpand(run1, run2):
    if run1['domain'] in domains_with_diff_of_translator_time_instantiating_for_mutexes_reducedexpand_larger_10:
        return run1['domain']
    return None

exp.add_report(
    ScatterPlotReport(
        filter_algorithm=[
            'translate-h2mutexes',
            'translate-reduced-h2mutexes-expand-nogoal',
        ],
        attributes=['translator_time_computing_h2_mutex_groups'],
        get_category=domain_category_for_mutexes_reducedexpand,
        format='tex',
    ),
    name='scatter-h2mutexes-time-regular-vs-reducedandexpand',
    outfile=os.path.join(exp.eval_dir, 'scatter-h2mutexes-time-regular-vs-reducedandexpand')
)

exp.run_steps()
