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
