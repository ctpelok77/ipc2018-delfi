#! /usr/bin/env python

from collections import deque, defaultdict
from itertools import combinations

import sys

import pddl
import timers

DEBUG = False

# (atom, True) positiv literal
# (atom, False) negative literal

def compute_all_pairs2(element_dict, only_positive_literals=False):
    if only_positive_literals:
        elements = dict(e for e in element_dict.items() if e[1] == True)
    else:
        elements = element_dict
    pairs = [frozenset([e]) for e in elements.items()]
    for pair in combinations(elements.items(), 2):
        pairs.append(frozenset(pair))
    return pairs

def extract_literals_from_condition2(condition):
    result = dict()
    if condition is None: # eg empty effect condition
        return result
    if isinstance(condition, list): # e.g. effect condition
        for cond in condition:
            result.update(extract_literals_from_condition2(cond))
    elif isinstance(condition, pddl.Literal):
        if condition.negated:
            result[condition.negate()] = False
        else:
            result[condition] = True
    else:
        print(condition)
        assert False
    return result



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
                    extract_literals_from_condition2(axiom.condition)
                condition_pairs = compute_all_pairs2(condition_literals,
                                                     only_positive_literals)
                add_rule(pair_to_rules, pair_index, rules, condition_pairs)
        else:
            literals = list(pair)
            literal1 = literals[0] # (atom, True) or (atom, False)
            literal2 = literals[1]
            if ((literal1[1] and literal1[0] == axiom.effect) or
                (literal2[1] and literal2[0] == axiom.effect)): #  3) axiom from which literal1 or literal2 can be derived
                condition_literals = extract_literals_from_condition2(axiom.condition)
                # Depending on which literal is made true by the axiom, add the other to condition_literals.
                if (literal1[1] and literal1[0] == axiom.effect):
                    if (literal1[0] in condition_literals and
                        condition_literals[literal1[0]] != literal1[1]):
                            continue
                    condition_literals[literal1[0]] = literal1[1]
                else:
                    if (literal2[0] in condition_literals and
                        condition_literals[literal2[0]] != literal2[1]):
                            continue
                    condition_literals[literal2[0]] = literal2[1]
                condition_pairs = compute_all_pairs2(condition_literals,
                                                     only_positive_literals)
                add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def is_consistent(literal_dict1, literal_dict2):
    # assume that each dict is consistent
    for (lit, val) in literal_dict1.items():
        if lit in literal_dict2 and literal_dict2[lit] != val:
            return False
    for (lit, val) in literal_dict2.items():
        if lit in literal_dict1 and literal_dict1[lit] != val:
            return False
    return True

def handle_operator_for_literal(literal, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_set, only_positive_literals):
    # Since l = l', there is no second effect phi' -> l', since l = l'.
    for condition in conditions_by_effect[literal]:
        # TODO the following four lines can be implemented more efficiently
        # together
        if not is_consistent(pre_set, condition):
            continue
        relevant_literals = pre_set.copy()
        relevant_literals.update(condition)

        if not literal[1]: # negative literal
            skip_rule = False
            for psi in conditions_by_effect[(literal[0], True)]:
                subset = True
                for atom, ispositive in psi.items():
                    if (not atom in relevant_literals or
                        relevant_literals[atom] != ispositive):
                        subset = False
                        break
                if subset:
                    skip_rule = True
                    break
            if skip_rule:
                continue

        condition_pairs = compute_all_pairs2(relevant_literals,
                                             only_positive_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)

def handle_operator_for_pair_single_effect(literal, preserve_literal, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_set, only_positive_literals):

    for phi in conditions_by_effect[literal]:
        if not is_consistent(pre_set, phi):
            continue
        relevant_literals = pre_set.copy()
        relevant_literals.update(phi)

        skip_rule = False
        for psi in conditions_by_effect[(preserve_literal[0], not preserve_literal[1])]:
            subset = True
            for atom, negated in psi.items():
                if (not atom in relevant_literals or
                    relevant_literals[atom] != negated):
                    subset = False
                    break
            if subset:
                skip_rule = True
                break
        if skip_rule:
            continue

        if (preserve_literal[0] in relevant_literals and
            relevant_literals[preserve_literal[0]] != preserve_literal[1]):
            # pre \land phi \land l' insconsistent
            continue
        relevant_literals[preserve_literal[0]] = preserve_literal[1]
        if not literal[1]: # literal is negative
            for psi in conditions_by_effect[(literal[0], True)]:
                subset = True
                for atom, negated in psi.items():
                    if (not atom in relevant_literals or
                        relevant_literals[atom] != negated):
                        subset = False
                        break
                if subset:
                    skip_rule = True
                    break
            if skip_rule:
                continue

        condition_pairs = compute_all_pairs2(relevant_literals,
                          only_positive_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_operator_for_pair(literal1, literal2, pair_to_rules, pair_index,
    rules, conditions_by_effect, pre_set, only_positive_literals):

    # first case: both possibly made true by operator
    for phi1 in conditions_by_effect[literal1]:
        if not is_consistent(pre_set, phi1):
            continue
        tmp_relevant_literals = pre_set.copy()
        tmp_relevant_literals.update(phi1)

        for phi2 in conditions_by_effect[literal2]:

            if not is_consistent(tmp_relevant_literals, phi2):
                continue
            relevant_literals = tmp_relevant_literals.copy()
            relevant_literals.update(phi2) # pre \cup phi1 \cup phi2

            if not literal1[1]: # literal1 is negative
                skip_rule = False
                for psi in conditions_by_effect[(literal1[0], True)]:
                    subset = True
                    for atom, negated in psi.items():
                        if (not atom in relevant_literals or
                            relevant_literals[atom] != negated):
                            subset = False
                            break
                    if subset:
                        skip_rule = True
                        break
                if skip_rule:
                    continue
            if not literal2[1]:
                skip_rule = False
                for psi in conditions_by_effect[(literal2[0], True)]:
                    subset = True
                    for atom, negated in psi.items():
                        if (not atom in relevant_literals or
                            relevant_literals[atom] != negated):
                            subset = False
                            break
                    if subset:
                        skip_rule = True
                        break
                if skip_rule:
                    continue

            condition_pairs = compute_all_pairs2(relevant_literals,
                only_positive_literals)
            add_rule(pair_to_rules, pair_index, rules, condition_pairs)

    # second case: one possibly made true whereas the other is preserved
    handle_operator_for_pair_single_effect(literal1, literal2, pair_to_rules,
        pair_index, rules, conditions_by_effect, pre_set, only_positive_literals)
    handle_operator_for_pair_single_effect(literal2, literal1, pair_to_rules,
        pair_index, rules, conditions_by_effect, pre_set, only_positive_literals)



def handle_operator(pairs, operator, pair_to_rules, rules, only_positive_literals):
    conditions_by_effect = defaultdict(list)
    for cond, eff in operator.add_effects:
        condition_literals = extract_literals_from_condition2(cond)
        conditions_by_effect[(eff, True)].append(condition_literals)
    for cond, eff in operator.del_effects:
        condition_literals = extract_literals_from_condition2(cond)
        conditions_by_effect[(eff, False)].append(condition_literals)
    pre_set = extract_literals_from_condition2(operator.precondition)

    for pair_index, pair in enumerate(pairs):
        if len(pair) == 1:
            handle_operator_for_literal(iter(pair).next(), pair_to_rules,
                pair_index, rules, conditions_by_effect, pre_set,
                only_positive_literals)
        else:
            literals = list(pair)
            handle_operator_for_pair(literals[0], literals[1], pair_to_rules,
                pair_index, rules, conditions_by_effect, pre_set,
                only_positive_literals)


def compute_reachability_program(atoms, actions, axioms, only_positive_literals):
    timer = timers.Timer()
    #print(atoms)
    literals = [(a,True) for a in atoms]
    if not only_positive_literals:
        for atom in atoms:
            literals.append((atom, False))
    # pair contains both "singleton pairs" and "real pairs".

    pairs = [frozenset([e]) for e in literals]
    for pair in combinations(literals, 2):
        pairs.append(frozenset(pair))

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
    sys.stdout.flush()
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
    initially_true_literals = dict()
    for atom in atoms:
        if atom in init:
            initially_true_literals[atom] = True
        elif not only_positive_literals:
            initially_true_literals[atom] = False
    initial_pairs = compute_all_pairs2(initially_true_literals)
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
    sys.stdout.flush()
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
    sys.stdout.flush()
    return mutex_pairs
