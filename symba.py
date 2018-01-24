#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from subprocess import call
import sys
import timers

parser = argparse.ArgumentParser()

parser.add_argument("planner")
parser.add_argument("domain_file")
parser.add_argument("problem_file")
parser.add_argument("plan_file")

args = parser.parse_args()
planner = args.planner
domain = args.domain_file
problem = args.problem_file
plan_file = args.plan_file

timer = timers.Timer()
call(['symba/src/plan-ipc', planner, domain, problem, plan_file])
print("Overall time: {}".format(timer))
