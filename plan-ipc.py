#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from subprocess import call
import sys

parser = argparse.ArgumentParser()

parser.add_argument(
    "--symba", action="store_true",
    help="run symba on the given domain and plan file, ignore all other arguments")
parser.add_argument("domain_file")
parser.add_argument("problem_file")
parser.add_argument("plan_file")

args = parser.parse_args()
domain = args.domain_file
problem = args.problem_file
plan_file = args.plan_file

if args.symba:
    call(['symba/plan', domain, problem, plan_file])
else:
    call([sys.executable, 'fast-downward.py', "--plan-file", plan_file, "--alias", "seq-opt-lmcut", domain, problem])
