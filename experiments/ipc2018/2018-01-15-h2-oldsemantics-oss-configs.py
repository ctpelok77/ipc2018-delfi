#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from lab.environments import LocalEnvironment, BaselSlurmEnvironment

from common_setup import IssueConfig, IssueExperiment, is_test_run

REVISION = '32fc46e415f3'

def main(revisions=None):
    benchmarks_dir = os.environ["DOWNWARD_BENCHMARKS"]

    # optimal suite
    # TODO: remove those adl domains that are compiled to axioms
    suite = ['airport', 'assembly', 'barman-opt11-strips',
    'barman-opt14-strips', 'blocks', 'cavediving-14-adl',
    'childsnack-opt14-strips', 'citycar-opt14-adl', 'depot', 'driverlog',
    'elevators-opt08-strips', 'elevators-opt11-strips',
    'floortile-opt11-strips', 'floortile-opt14-strips', 'freecell',
    'ged-opt14-strips', 'grid', 'gripper', 'hiking-opt14-strips',
    'logistics00', 'logistics98', 'maintenance-opt14-adl', 'miconic',
    'miconic-fulladl', 'miconic-simpleadl', 'movie', 'mprime', 'mystery',
    'nomystery-opt11-strips', 'openstacks', 'openstacks-opt08-adl',
    'openstacks-opt08-strips', 'openstacks-opt11-strips',
    'openstacks-opt14-strips', 'openstacks-strips', 'optical-telegraphs',
    'parcprinter-08-strips', 'parcprinter-opt11-strips',
    'parking-opt11-strips', 'parking-opt14-strips', 'pathways',
    'pathways-noneg', 'pegsol-08-strips', 'pegsol-opt11-strips',
    'philosophers', 'pipesworld-notankage', 'pipesworld-tankage', 'psr-large',
    'psr-middle', 'psr-small', 'rovers', 'satellite', 'scanalyzer-08-strips',
    'scanalyzer-opt11-strips', 'schedule', 'sokoban-opt08-strips',
    'sokoban-opt11-strips', 'storage', 'tetris-opt14-strips',
    'tidybot-opt11-strips', 'tidybot-opt14-strips', 'tpp',
    'transport-opt08-strips', 'transport-opt11-strips',
    'transport-opt14-strips', 'trucks', 'trucks-strips',
    'visitall-opt11-strips', 'visitall-opt14-strips',
    'woodworking-opt08-strips', 'woodworking-opt11-strips', 'zenotravel']

    environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    if is_test_run():
        suite = ['gripper:prob01.pddl','gripper:prob02.pddl']
        environment = LocalEnvironment(processes=4)

    configs = {
        IssueConfig('h2-oldsemantics-oss-blind', ['--translate-options', '--enforce-definite-effects', '--search-options', '--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(blind,symmetries=sym)'], driver_options=['--transform', 'h2-mutexes']),
        IssueConfig('h2-oldsemantics-oss-celmcut', ['--translate-options', '--enforce-definite-effects', '--search-options', '--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(celmcut,symmetries=sym)'], driver_options=['--transform', 'h2-mutexes']),
        # IssueConfig('h2-oldsemantics-oss-lmcount', ['--translate-options', '--enforce-definite-effects', '--search-options', '--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(lmcount(lm_factory=,admissible=true),symmetries=sym)'], driver_options=['--transform', 'h2-mutexes']),
        # TODO: M&S
        # TODO: iPDB/PDB: no support for conditional effects
    }

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )
    exp.add_suite(benchmarks_dir, suite)

    exp.add_absolute_report_step()

    exp.run_steps()

main(revisions=[REVISION])
