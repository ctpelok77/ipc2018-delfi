#! /usr/bin/env python

from collections import deque, defaultdict
from itertools import combinations

import pddl
import timers

DEBUG = False

def compute_all_pairs(elements):
    """ Return a list of unordered pairs of elements from *elements*, including
    'singleton pairs'."""
    pairs = [frozenset([e]) for e in elements]
    for pair in combinations(elements, 2):
        pairs.append(frozenset(pair))
    return pairs


def extract_literals_from_condition(condition, only_positive_literals):
    if condition is None:
        return []
    condition_literals = []
    if isinstance(condition, list):
        for cond in condition:
            condition_literals.extend(extract_literals_from_condition(cond,
                only_positive_literals))
    elif isinstance(condition, pddl.Conjunction):
        for literal in condition.parts:
            if not only_positive_literals or not literal.negated:
                condition_literals.append(literal)
    elif isinstance(condition, pddl.Literal):
        if not only_positive_literals or not condition.negated:
            condition_literals.append(condition)
    else:
        print(condition)
        assert False
    return condition_literals


def add_rule(pair_to_rules, pair_index, rules, condition_pairs):
    for cond_pair in condition_pairs:
        pair_to_rules[cond_pair].append(len(rules)) # fails if cond_pair is unknown
        if DEBUG:
            print("adding rule index {} to pair".format(len(rules)))
    if DEBUG:
        print("adding rule with body {}".format(condition_pairs))
    rules.append([pair_index, len(condition_pairs)])


def handle_axiom(pairs, axiom, pair_to_rules, rules, only_positive_literals):
    assert isinstance(axiom.effect, pddl.Literal)
    for pair_index, pair in enumerate(pairs):
        if len(pair) == 1:
            literal = iter(pair).next()
            if literal == axiom.effect: # 2) axiom from which literal can be derived
                condition_literals = \
                set(extract_literals_from_condition(axiom.condition,
                                                    only_positive_literals))
                condition_pairs = compute_all_pairs(condition_literals)
                add_rule(pair_to_rules, pair_index, rules, condition_pairs)
        else:
            literals = list(pair)
            literal1 = literals[0]
            literal2 = literals[1]
            if literal1 == axiom.effect or literal2 == axiom.effect: #  3) axiom from which literal1 or literal2 can be derived
                condition_literals = set(extract_literals_from_condition(axiom.condition,only_positive_literals))
                # Depending on which literal is made true by the axiom, add the other to condition_literals.
                if literal1 == axiom.effect:
                    condition_literals.add(literal2)
                else:
                    condition_literals.add(literal1)
                condition_pairs = compute_all_pairs(condition_literals)
                add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_operator_for_literal(literal, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_set):

    # Since l = l', there is no second effect phi' -> l', since l = l'.
    atom = literal
    negative = False
    if literal.negated:
        negative = True
        atom = literal.negate()

    for condition in conditions_by_effect[(atom,  not negative)]:
        relevant_literals = pre_set | condition

        if negative:
            skip_rule = False
            for psi in conditions_by_effect[(atom, True)]:
                if psi <= relevant_literals:
                    skip_rule = True
                    break
            if skip_rule:
                continue

        condition_pairs = compute_all_pairs(relevant_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)

def handle_operator_for_pair_single_effect(literal, preserve_literal, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_set):

    atom = literal
    negative = False
    if literal.negated:
        negative = True
        atom = literal.negate()

    preserve_atom = preserve_literal
    preserve_negative = False
    if preserve_literal.negated:
        preserve_negative = True
        preserve_atom = preserve_literal.negate()

    for phi in conditions_by_effect[(atom, not negative)]:
        relevant_literals = pre_set | phi
        skip_rule = False
        for psi in conditions_by_effect[(preserve_atom, preserve_negative)]:
            if psi <= relevant_literals:
                skip_rule = True
                break
        if skip_rule:
            continue

        relevant_literals.add(preserve_literal)
        if negative:
            for psi in conditions_by_effect[(atom, True)]:
                if psi <= relevant_literals:
                    skip_rule = True
                    break
            if skip_rule:
                continue

        condition_pairs = compute_all_pairs(relevant_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_operator_for_pair(literal1, literal2, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_set):

    # first case: both possibly made true by operator
    atom1, atom2 = literal1, literal2
    negative1, negative2 = False, False
    if literal1.negated:
        negative1 = True
        atom1 = literal1.negate()
    if literal2.negated:
        negative2 = True
        atom2 = literal2.negate()

    for phi1 in conditions_by_effect[(atom1, not negative1)]:
        for phi2 in conditions_by_effect[(atom2, not negative2)]:

            relevant_literals = pre_set | phi1 | phi2

            if negative1:
                skip_rule = False
                for psi in conditions_by_effect[(atom1, True)]:
                    if psi <= relevant_literals:
                        skip_rule = True
                        break
                if skip_rule:
                    continue
            if negative2:
                skip_rule = False
                for psi in conditions_by_effect[(atom2, True)]:
                    if psi <= relevant_literals:
                        skip_rule = True
                        break
                if skip_rule:
                    continue

            condition_pairs = compute_all_pairs(relevant_literals)
            add_rule(pair_to_rules, pair_index, rules, condition_pairs)

    # second case: one possibly made true whereas the other is preserved
    handle_operator_for_pair_single_effect(literal1, literal2, pair_to_rules,
        pair_index, rules, conditions_by_effect, pre_set)
    handle_operator_for_pair_single_effect(literal2, literal1, pair_to_rules,
        pair_index, rules, conditions_by_effect, pre_set)



def handle_operator(pairs, operator, pair_to_rules, rules, only_positive_literals):
    conditions_by_effect = defaultdict(set)
    for cond, eff in operator.add_effects:
        condition_literals = extract_literals_from_condition(cond, only_positive_literals)
        conditions_by_effect[(eff, True)].add(frozenset(condition_literals))
    for cond, eff in operator.del_effects:
        condition_literals = extract_literals_from_condition(cond, only_positive_literals)
        conditions_by_effect[(eff.negate(), False)].add(frozenset(condition_literals))
    pre_set = set(extract_literals_from_condition(operator.precondition, only_positive_literals))

    for pair_index, pair in enumerate(pairs):
        if len(pair) == 1:
            handle_operator_for_literal(iter(pair).next(), pair_to_rules,
                pair_index, rules, conditions_by_effect, pre_set)
        else:
            literals = list(pair)
            handle_operator_for_pair(literals[0], literals[1], pair_to_rules,
                pair_index, rules, conditions_by_effect, pre_set)


def compute_reachability_program(atoms, actions, axioms, only_positive_literals):
    timer = timers.Timer()
    #print(atoms)
    literals = list(atoms)
    if not only_positive_literals:
        for atom in atoms:
            literals.append(atom.negate())
    # pair contains both "singleton pairs" and "real pairs".
    pairs = compute_all_pairs(literals)
#    print(pairs)

    rules = []
    pair_to_rules = {}
    # Manually set empty list for each pair to enforce key errors when
    # attempting to access unknown pairs later.
    for pair in pairs:
        pair_to_rules[pair] = []

    for op in actions:
        handle_operator(pairs, op, pair_to_rules, rules, only_positive_literals)
    for ax in axioms:
        handle_axiom(pairs, ax, pair_to_rules, rules, only_positive_literals)
    print("Time to compute h2 mutexes reachability program: {}s".format(timer.elapsed_time()))
    return pairs, pair_to_rules, rules


def compute_mutex_pairs(task, atoms, actions, axioms, reachable_action_params,
    only_positive_literals=False):
    pairs, pair_to_rules, rules = compute_reachability_program(atoms, actions,
        axioms, only_positive_literals)

    if DEBUG:
        for key,val in pair_to_rules.items():
            print(key, val)

        for rule in rules:
            pair = pairs[rule[0]]
            num_conditions = rule[1]
            print("{} <- {}".format(pair, num_conditions))

    timer = timers.Timer()
    open_list = deque()
    closed = set()
    init = set(task.init)
    init &= atoms
    initially_true_literals = []
    for atom in atoms:
        if atom in init:
            initially_true_literals.append(atom)
        elif not only_positive_literals:
            initially_true_literals.append(atom.negate())
    initial_pairs = compute_all_pairs(initially_true_literals)
    for pair in initial_pairs:
        assert pair not in closed
        open_list.append(pair)
        closed.add(pair)
    while len(open_list):
        pair = open_list.popleft()
        #print("pop pair {}".format(pair))
        for rule_index in pair_to_rules[pair]:
            rule = rules[rule_index]
            #print("deal with rule index {} which is rule {}".format(rule_index, rule))
            assert(rule[1] > 0)
            rule[1] = rule[1] - 1

            if rule[1] == 0:
                # handle applicable rule (the test against closed prevents
                # rules from being handled more than once)
                new_pair = pairs[rule[0]]
                #print("new pair {}".format(new_pair))
                if new_pair not in closed: # already dealt with new_pair
                    #print("must be queued")
                    closed.add(new_pair)
                    open_list.append(new_pair)

    print("Found {} reachable pairs of literals".format(len(closed)))
    if DEBUG:
        for pair in closed:
            for lit in pair:
                print(lit),
            print

    mutex_pairs = []
    for pair in pairs:
        if pair not in closed:
            mutex_pairs.append(pair)
    print("Found {} unreachable pairs of literals".format(len(mutex_pairs)))
    if DEBUG:
        for pair in mutex_pairs:
            for lit in pair:
                print(lit),
            print

    print("Time to compute model of reachability program: {}s".format(timer.elapsed_time()))
    return mutex_pairs
