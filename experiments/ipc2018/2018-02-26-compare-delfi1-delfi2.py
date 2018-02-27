#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport
from common_setup import IssueConfig, IssueExperiment, is_test_run

def main(revisions=[]):
    benchmarks_dir = os.environ["DOWNWARD_BENCHMARKS_IPC2018"]

    # optimal strips suite
    suite = ['airport', 'barman-opt11-strips', 'barman-opt14-strips', 'blocks',
    'childsnack-opt14-strips', 'depot', 'driverlog', 'elevators-opt08-strips',
    'elevators-opt11-strips', 'floortile-opt11-strips',
    'floortile-opt14-strips', 'freecell', 'ged-opt14-strips', 'grid',
    'gripper', 'hiking-opt14-strips', 'logistics00', 'logistics98', 'miconic',
    'movie', 'mprime', 'mystery', 'nomystery-opt11-strips',
    'openstacks-opt08-strips', 'openstacks-opt11-strips',
    'openstacks-opt14-strips', 'openstacks-strips', 'parcprinter-08-strips',
    'parcprinter-opt11-strips', 'parking-opt11-strips', 'parking-opt14-strips',
    'pathways-noneg', 'pegsol-08-strips', 'pegsol-opt11-strips',
    'pipesworld-notankage', 'pipesworld-tankage', 'psr-small', 'rovers',
    'satellite', 'scanalyzer-08-strips', 'scanalyzer-opt11-strips',
    'sokoban-opt08-strips', 'sokoban-opt11-strips', 'storage',
    'tetris-opt14-strips', 'tidybot-opt11-strips', 'tidybot-opt14-strips',
    'tpp', 'transport-opt08-strips', 'transport-opt11-strips',
    'transport-opt14-strips', 'trucks-strips', 'visitall-opt11-strips',
    'visitall-opt14-strips', 'woodworking-opt08-strips',
    'woodworking-opt11-strips', 'zenotravel',]
    # extra strips domains
    suite.extend(['ss_barman', 'ss_ferry', 'ss_goldminer', 'ss_grid',
    'ss_hanoi', 'ss_hiking', 'ss_npuzzle', 'ss_spanner',])
    # conditional effects suite
    suite.extend(['briefcaseworld', 'cavediving-14-adl', 'citycar-opt14-adl',
    'fsc-blocks', 'fsc-grid-a1', 'fsc-grid-a2', 'fsc-grid-r', 'fsc-hall',
    'fsc-visualmarker', 'gedp-ds2ndp', 'miconic-simpleadl', 't0-adder',
    't0-coins', 't0-comm', 't0-grid-dispose', 't0-grid-push', 't0-grid-trash',
    't0-sortnet', 't0-sortnet-alt', 't0-uts',])
    # extra conditional effects domains
    suite.extend(['ss_briefcaseworld', 'ss_cavediving', 'ss_citycar',
    'ss_maintenance', 'ss_maintenance_large', 'ss_schedule',])

    if is_test_run():
        suite = ['gripper:prob01.pddl', 'miconic-simpleadl:s1-0.pddl']
        environment = LocalEnvironment(processes=4)
    else:
        environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    configs = {}

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)

    def renamedelfi1(props):
        props['algorithm'] = 'delfi1'
        id = props['id']
        id[0] = 'delfi1'
        props['id'] = id
        return props

    def renamedelfi2(props):
        props['algorithm'] = 'delfi2'
        id = props['id']
        id[0] = 'delfi2'
        props['id'] = id
        return props
    exp.add_fetcher('data/2018-02-26-delfi1-fulltrainingset-eval',filter=renamedelfi1)
    exp.add_fetcher('data/2018-02-26-delfi2-fulltrainingset-eval',filter=renamedelfi2)

    attributes = [
        'cost', 'coverage', 'error', 'memory', 'plan_length', 'planner',
        'search_time', 'total_time',
    ]

    exp.add_report(
        ComparativeReport(
            algorithm_pairs=[
                ('delfi1', 'delfi2'),
            ],
            attributes=attributes,
        ),
        outfile=os.path.join(exp.eval_dir, exp.name + '.html'),
    )

    exp.run_steps()

main()
