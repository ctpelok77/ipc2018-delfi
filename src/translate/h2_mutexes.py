#! /usr/bin/env python

from collections import defaultdict, deque

import pddl

DEBUG = False

def compute_all_pairs(elements):
    assert isinstance(elements, list)
    pairs = []
    for index1 in range(len(elements)):
        elem1 = elements[index1]
        pairs.append(frozenset([elem1]))
        for index2 in range(index1 + 1, len(elements)):
            elem2 = elements[index2]
            pairs.append(frozenset([elem1, elem2]))
    return pairs


def extract_literals_from_condition(condition):
    if condition is None:
        return []
    condition_literals = []
    if isinstance(condition, list):
        for cond in condition:
            condition_literals.extend(extract_literals_from_condition(cond))
    elif isinstance(condition, pddl.Conjunction):
        for literal in condition.parts:
            condition_literals.append(literal)
    elif isinstance(condition, pddl.Literal):
        condition_literals.append(condition)
    else:
        print(condition)
        assert False
    return condition_literals


def add_rule(pair_to_rules, pair_index, rules, condition_pairs):
    for cond_pair in condition_pairs:
        assert cond_pair in pair_to_rules.keys()
        pair_to_rules[cond_pair].append(len(rules))
        if DEBUG:
            print("adding rule index {} to pair".format(len(rules)))
    if DEBUG:
        print("adding rule with body {}".format(condition_pairs))
    rules.append([pair_index, len(condition_pairs)])


def add_literals_if_not_present(literals, condition):
    for lit in extract_literals_from_condition(condition):
        if lit not in literals:
            literals.append(lit)


def all_literals_contained(literals, condition):
    for lit in extract_literals_from_condition(condition):
        if lit not in literals:
            return False
    return True


def has_op_satisfied_add_effect_on_literal(literal, operator, condition_literals):
    for add_cond, add_eff in operator.add_effects:
        if add_eff == literal:
            if all_literals_contained(condition_literals, add_cond):
                return True
    return False


def handle_axiom_for_literal(literal, axiom, pair_to_rules, pair_index, rules):
    assert isinstance(axiom.effect, pddl.Literal)
    if literal == axiom.effect: # 2) axiom from which literal can be derived
        condition_literals = extract_literals_from_condition(axiom.condition)
        condition_pairs = compute_all_pairs(condition_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_operator_for_literal(literal, operator, pair_to_rules, pair_index, rules):
    # TODO: is this complete and correct? there is no second effect phi' -> l', since l = l'
    for cond, eff in operator.add_effects:
        if literal == eff: # 4) operator makes l true
            relevant_literals = extract_literals_from_condition(operator.precondition)
            add_literals_if_not_present(relevant_literals, cond)
            condition_pairs = compute_all_pairs(relevant_literals)
            add_rule(pair_to_rules, pair_index, rules, condition_pairs)

    for cond, eff in operator.del_effects:
        del_eff = eff.negate()
        if literal == del_eff: # 4) operator makes ~literal false, i.e. literal true
            relevant_literals = extract_literals_from_condition(operator.precondition)
            add_literals_if_not_present(relevant_literals, cond)

            # check case 3 of 4)
            negated_lit = literal.negate()
            for add_cond, add_eff in operator.add_effects:
                if add_eff == negated_lit:
                    if not all_literals_contained(literals, add_cond):
                        condition_pairs = compute_all_pairs(relevant_literals)
                        add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_axiom_for_pair(literal1, literal2, axiom, pair_to_rules, pair_index, rules):
    assert isinstance(axiom.effect, pddl.Literal)
    if literal1 == axiom.effect or literal2 == axiom.effect: #  3) axiom from which literal1 or literal2 can be derived
        condition_literals = extract_literals_from_condition(axiom.condition)
        if literal1 == axiom.effect:
            if literal2 not in condition_literals:
                condition_literals.append(literal2)
        else:
            if literal1 not in condition_literals:
                condition_literals.append(literal1)
        condition_pairs = compute_all_pairs(condition_literals)
        add_rule(pair_to_rules, pair_index, rules, condition_pairs)


def handle_operator_for_pair(literal1, literal2, operator, pair_to_rules, pair_index, rules):
    lit1_effects = []
    lit2_effects = []
    for cond, eff in operator.add_effects:
        if literal1 == eff:
            lit1_effects.append((cond, True))
        if literal2 == eff:
            lit2_effects.append((cond, True))
    for cond, eff in operator.del_effects:
        neg_eff = eff.negate()
        if literal1 == eff:
            lit1_effects.append((cond, False))
        if literal2 == eff:
            lit2_effects.append((cond, False))

    if lit1_effects and lit2_effects: # 4) operator makes both literal1 and literal2 true
        # go over all pairs of effects that make both literals true
        for lit1_eff in lit1_effects:
            for lit2_eff in lit2_effects:
                condition_literals = extract_literals_from_condition(operator.precondition)
                for cond in [lit1_eff[0], lit2_eff[0]]:
                    add_literals_if_not_present(condition_literals, cond)

                overwriting_add_effect_lit1 = False
                if not lit1_eff[1]: # case 3 of 4) for literal1 (delete effect)
                    overwriting_add_effect_lit1 = has_op_satisfied_add_effect_on_literal(literal1.negate(), operator, condition_literals)

                if not overwriting_add_effect_lit1:
                    overwriting_add_effect_lit2 = False
                    if not lit2_eff[1]: # case 3 of 4) for literal2 (delete effect)
                        overwriting_add_effect_lit2 = has_op_satisfied_add_effect_on_literal(literal2.negate(), operator, condition_literals)

                    if not overwriting_add_effect_lit2:
                        condition_pairs = compute_all_pairs(condition_literals)
                        add_rule(pair_to_rules, pair_index, rules, condition_pairs)

    elif lit1_effects or lit2_effects: # 5) operator only makes true one of literal1 and literal2
        for lit1_eff in lit1_effects:
            condition_literals = extract_literals_from_condition(operator.precondition)
            add_literals_if_not_present(condition_literals, lit1_eff[0])

            # check case 4 of 5) for literal1 first, since we need to test against phi \land \pre(o) only
            negated_lit2 = literal2.negate()
            overwriting_add_effect_lit2 = has_op_satisfied_add_effect_on_literal(literal2.negate(), operator, condition_literals)

            if not overwriting_add_effect_lit2:
                # add literal2 to relevant literals (required for case 2 and 3 of 5))
                if literal2 not in condition_literals:
                    condition_literals.append(literal2)

                overwriting_add_effect_lit1 = False
                if not lit1_eff[1]: # case 3 of 5) for literal1 (delete effect)
                    overwriting_add_effect_lit1 = has_op_satisfied_add_effect_on_literal(literal1.negate(), operator, condition_literals)

                if not overwriting_add_effect_lit1:
                    condition_pairs = compute_all_pairs(condition_literals)
                    add_rule(pair_to_rules, pair_index, rules, condition_pairs)

        # TODO: symmetric case missing


def compute_reachability_program(atoms, actions, axioms):
    literals = list(atoms)
    for atom in atoms:
        literals.append(atom.negate())
    pairs = compute_all_pairs(literals)

    pair_to_rules = {} #defaultdict(list)
    for pair in pairs:
        pair_to_rules[pair] = [] # to assert that each pair inserted is known

    rules = []
    for pair_index, pair in enumerate(pairs):
        if DEBUG:
            print("considering pair {}".format(pair))
        if len(pair) == 1: # l = l'
            literal = list(pair)[0]

            for ax in axioms:
                if DEBUG:
                    print("considering axiom"),
                    ax.dump()
                handle_axiom_for_literal(literal, ax, pair_to_rules, pair_index, rules)

            for op in actions:
                if DEBUG:
                    print("considering action:"),
                    op.dump()
                handle_operator_for_literal(literal, op, pair_to_rules, pair_index, rules)

        else: # l != l'
            literal1 = list(pair)[0]
            literal2 = list(pair)[1]
            assert literal1 != literal2

            for ax in axioms:
                if DEBUG:
                    print("considering axiom"),
                    ax.dump()
                handle_axiom_for_pair(literal1, literal2, ax, pair_to_rules, pair_index, rules)

            for op in actions:
                if DEBUG:
                    print("considering action:"),
                    op.dump()
                handle_operator_for_pair(literal1, literal2, op, pair_to_rules, pair_index, rules)

    return pairs, pair_to_rules, rules


def compute_mutex_pairs(task, atoms, actions, axioms, reachable_action_params):
    pairs, pair_to_rules, rules = compute_reachability_program(atoms, actions, axioms)

    if DEBUG:
        for key,val in pair_to_rules.items():
            print(key, val)

        for rule in rules:
            pair = pairs[rule[0]]
            num_conditions = rule[1]
            print("{} <- {}".format(pair, num_conditions))

    open_list = deque()
    closed = set()
    initial_pairs = compute_all_pairs(task.init)
    for pair in initial_pairs:
        assert pair not in closed
        open_list.append(pair)
        closed.add(pair)
    while len(open_list):
        pair = open_list.popleft()
        #print("pop pair {}".format(pair))
        if pair in pair_to_rules.keys():
            for rule_index in pair_to_rules[pair]:
                rule = rules[rule_index]
                #print("deal with rule index {} which is rule {}".format(rule_index, rule))
                if rule[1] > 0: # rule is not applicable yet
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

    return closed
