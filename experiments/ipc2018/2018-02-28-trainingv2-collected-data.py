#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from lab.environments import LocalEnvironment, BaselSlurmEnvironment
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport
from common_setup import IssueConfig, IssueExperiment, is_test_run

def main(revisions=[]):
    if is_test_run():
        environment = LocalEnvironment(processes=4)
    else:
        environment = BaselSlurmEnvironment(email="silvan.sievers@unibas.ch", export=["PATH"])

    configs = {}

    exp = IssueExperiment(
        revisions=revisions,
        configs=configs,
        environment=environment,
    )

    exp.add_fetcher(os.path.expanduser('~/data/2018-02-22-trainingv1-alternative-ms-planners-mk-eval'))
    exp.add_fetcher(os.path.expanduser('~/data/2018-02-28-trainingv1-dks-part1-mk-eval'),merge=True)
    exp.add_fetcher(os.path.expanduser('~/data/2018-02-28-trainingv1-dks-part2-mk-eval'),merge=True)
    exp.add_fetcher(os.path.expanduser('~/data/2018-02-28-trainingv1-oss-part1-mk-eval'),merge=True)
    exp.add_fetcher(os.path.expanduser('~/data/2018-02-28-trainingv1-oss-part2-mk-eval'),merge=True)
    exp.add_fetcher(os.path.expanduser('~/data/2018-02-27-trainingv1-symba-mk-eval'),merge=True)

    attributes = [
        'cost', 'coverage', 'error', 'memory', 'plan_length', 'planner',
        'run_dir', 'search_time', 'total_time',
    ]

    REV1 = '1b3fcd1654b3'
    REV2 = '5652d59dafed'
    exp.add_absolute_report_step(attributes=attributes,filter_algorithm=[
        '{}-h2-simpless-dks-blind'.format(REV1),
        '{}-h2-simpless-dks-celmcut'.format(REV1),
        '{}-h2-simpless-dks-lmcountlmrhw'.format(REV1),
        '{}-h2-simpless-dks-lmcountlmmergedlmrhwlmhm1'.format(REV1),
        '{}-h2-simpless-dks-900masb50ksccdfp'.format(REV2),
        '{}-h2-simpless-dks-900masb50ksbmiasm'.format(REV2),
        '{}-simpless-dks-900masb50kmiasmdfp'.format(REV2),
        '{}-h2-simpless-dks-900masginfsccdfp'.format(REV2),
        '{}-h2-simpless-dks-cpdbshc900'.format(REV1),
        '{}-h2-simpless-dks-zopdbsgenetic'.format(REV1),
        '{}-h2-simpless-oss-blind'.format(REV1),
        '{}-h2-simpless-oss-celmcut'.format(REV1),
        '{}-h2-simpless-oss-900masb50ksccdfp'.format(REV2),
        '{}-h2-simpless-oss-900masb50ksbmiasm'.format(REV2),
        '{}-simpless-oss-900masb50kmiasmdfp'.format(REV2),
        '{}-h2-simpless-oss-900masginfsccdfp'.format(REV2),
        '{}-h2-simpless-oss-cpdbshc900'.format(REV1),
        '{}-h2-simpless-oss-zopdbsgenetic'.format(REV1),
        'seq-opt-symba-1',
    ])

    exp.run_steps()

main()
