#! /usr/bin/env python

from collections import defaultdict

import pddl

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


def add_rule(pairs_to_rules, pair_index, rules, condition_pairs, pair_set):
    """ *pair_set* only used for assertions"""
    for cond_pair in condition_pairs:
        assert cond_pair in pair_set
        pairs_to_rules[cond_pair] = len(rules)
    rules.append((pair_index, len(condition_pairs)))


def compute_reachability_program(atoms, actions, axioms):
    #print(atoms)
    #for action in actions:
        #action.dump()
    #for axiom in axioms:
        #axiom.dump()
    #print(reachable_action_params)

    literals = list(atoms)
    for atom in atoms:
        literals.append(atom.negate())
    pairs = compute_all_pairs(literals)
    pair_set = set(pairs) # only for assertions

    pairs_to_rules = defaultdict(list)
    rules = []
    for index, pair in enumerate(pairs):
        if len(pair) == 1: # l = l'
            literal = list(pair)[0]

            for ax in axioms:
                assert isinstance(ax.effect, pddl.Literal)
                if literal == ax.effect: # 2) axiom from which literal can be derived
                    condition_literals = extract_literals_from_condition(ax.condition)
                    condition_pairs = compute_all_pairs(condition_literals)
                    add_rule(pairs_to_rules, index, rules, condition_pairs, pair_set)

            for op in actions:
                # TODO: is this complete and correct? there is no second effect phi' -> l', since l = l'
                for cond, eff in op.add_effects:
                    if literal == eff: # 4) operator makes l true
                        relevant_literals = extract_literals_from_condition(op.precondition)
                        for lit in extract_literals_from_condition(cond):
                            if lit not in relevant_literals:
                                relevant_literals.append(lit)
                        condition_pairs = compute_all_pairs(relevant_literals)
                        add_rule(pairs_to_rules, index, rules, condition_pairs, pair_set)

                for cond, eff in op.del_effects:
                    del_eff = eff.negate()
                    if literal == del_eff: # 4) operator makes ~literal false, i.e. literal true
                        relevant_literals = extract_literals_from_condition(op.precondition)
                        for lit in extract_literals_from_condition(cond):
                            if lit not in relevant_literals:
                                relevant_literals.append(lit)

                        negated_lit = literal.negate()
                        # check case 3 of 4)
                        for add_cond, add_eff in op.add_effects:
                            if add_eff == negated_lit:
                                all_literals_contained = True
                                for lit in extract_literals_from_condition(add_cond):
                                    if lit not in relevant_literals:
                                        all_literals_contained = False
                                        break
                                if not all_literals_contained:
                                    condition_pairs = compute_all_pairs(relevant_literals)
                                    add_rule(pairs_to_rules, index, rules, condition_pairs, pair_set)

        else: # l != l'
            literal1 = list(pair)[0]
            literal2 = list(pair)[1]
            assert literal1 != literal2

            for ax in axioms:
                assert isinstance(ax.effect, pddl.Literal)
                if literal1 == ax.effect or literal2 == ax.effect: #  3) axiom from which literal1 or literal2 can be derived
                    condition_literals = extract_literals_from_condition(ax.condition)
                    if literal1 == ax.effect:
                        if literal2 not in condition_literals:
                            condition_literals.append(literal2)
                    else:
                        if literal1 not in condition_literals:
                            condition_literals.append(literal1)
                    condition_pairs = compute_all_pairs(condition_literals)
                    add_rule(pairs_to_rules, index, rules, condition_pairs, pair_set)


            for op in actions:
                lit1_effects = []
                lit2_effects = []
                for cond, eff in op.add_effects:
                    if literal1 == eff:
                        lit1_effects.append((cond, True))
                    if literal2 == eff:
                        lit2_effects.append((cond, True))
                for cond, eff in op.del_effects:
                    neg_eff = eff.negate()
                    if literal1 == eff:
                        lit1_effects.append((cond, False))
                    if literal2 == eff:
                        lit2_effects.append((cond, False))

                if lit1_effects and lit2_effects: # 4) operator makes both literal1 and literal2 true
                    # go over all pairs of effects that make both literals true
                    for lit1_eff in lit1_effects:
                        for lit2_eff in lit2_effects:
                            relevant_literals = extract_literals_from_condition(op.precondition)
                            for cond in [lit1_eff[0], lit2_eff[0]]:
                                for lit in extract_literals_from_condition(cond):
                                    if lit not in relevant_literals:
                                        relevant_literals.append(lit)

                            overwriting_add_effect_lit1 = False
                            if not lit1_eff[1]: # case 3 of 4) for literal1 (delete effect)
                                negated_lit1 = literal1.negate()
                                for add_cond, add_eff in op.add_effects:
                                    if add_eff == negated_lit1:
                                        all_literals_contained = True
                                        for lit in extract_literals_from_condition(add_cond):
                                            if lit not in relevant_literals:
                                                all_literals_contained = False
                                                break
                                        if all_literals_contained:
                                            overwriting_add_effect_lit1 = True
                                            break

                            overwriting_add_effect_lit2 = False
                            if not lit2_eff[1]: # case 3 of 4) for literal2 (delete effect)
                                negated_lit2 = literal2.negate()
                                for add_cond, add_eff in op.add_effects:
                                    if add_eff == negated_lit2:
                                        all_literals_contained = True
                                        for lit in extract_literals_from_condition(add_cond):
                                            if lit not in relevant_literals:
                                                all_literals_contained = False
                                                break
                                        if all_literals_contained:
                                            overwriting_add_effect_lit2 = True
                                            break

                            if not overwriting_add_effect_lit1 and not overwriting_add_effect_lit2:
                                condition_pairs = compute_all_pairs(relevant_literals)
                                add_rule(pairs_to_rules, index, rules, condition_pairs, pair_set)



                elif lit1_effects or lit2_effects: # 5) operator only makes true one of literal1 and literal2
                    for lit1_eff in lit1_effects:
                        relevant_literals = extract_literals_from_condition(op.precondition)
                        for lit in extract_literals_from_condition(lit1_eff[0]):
                            if lit not in relevant_literals:
                                relevant_literals.append(lit)

                        # check case 4 of 5) for literal1 first, since we need to test against phi \land \pre(o) only
                        negated_lit2 = literal2.negate()
                        overwriting_add_effect_lit2 = False
                        for add_cond, add_eff in op.add_effects:
                            if add_eff == negated_lit2:
                                all_literals_contained = True
                                for lit in extract_literals_from_condition(add_cond):
                                    if lit not in relevant_literals:
                                        all_literals_contained = False
                                        break
                                if all_literals_contained:
                                    overwriting_add_effect_lit2 = True # skip rule entirely
                                    break

                        if not overwriting_add_effect_lit2:
                            # add literal2 to relevant literals (see case 2 and 3 of 5))
                            if literal2 not in relevant_literals:
                                relevant_literals.append(literal2)

                            overwriting_add_effect_lit1 = False
                            if not lit1_eff[1]: # case 3 of 5) for literal1 (delete effect)
                                negated_lit1 = literal1.negate()

                                for add_cond, add_eff in op.add_effects:
                                    if add_eff == negated_lit1:
                                        all_literals_contained = True
                                        for lit in extract_literals_from_condition(add_cond):
                                            if lit not in relevant_literals:
                                                all_literals_contained = False
                                                break
                                        if all_literals_contained:
                                            overwriting_add_effect_lit1 = True # skip rule entirely
                                            break

                            if not overwriting_add_effect_lit1:
                                condition_pairs = compute_all_pairs(relevant_literals)
                                add_rule(pairs_to_rules, index, rules, condition_pairs, pair_set)

    #for pair_index, num_conditions in rules:
        #print("{} <- {}".format(pairs[pair_index], num_conditions))

    #print(rules)
    return pairs_to_rules, rules


def compute_mutex_pairs(task, atoms, actions, axioms, reachable_action_params):
    pairs_to_rules, rules = compute_reachability_program(atoms, actions, axioms)

    result = []
    return result
