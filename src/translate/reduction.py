#! /usr/bin/env python

from collections import defaultdict

import build_model
import normalize
import pddl
import pddl_to_prolog

def compute_param_condition_to_rule_body(condition):
    param_to_body = defaultdict(set)

    if isinstance(condition, pddl.Conjunction):
        for literal in condition.parts:
            for index, param in enumerate(literal.args):
                param_to_body[param].add((literal.predicate, index))
    elif isinstance(condition, pddl.Literal):
        literal = condition
        for index, param in enumerate(literal.args):
            param_to_body[param].add((literal.predicate, index))
    elif isinstance(condition, pddl.Truth):
        pass
    else:
        assert False

    return param_to_body

def build_reachability_program(task, objects):
    def get_atom(key):
        if key not in tuple_to_atom:
            tuple_to_atom[key] = pddl.Atom(key, ())
        return tuple_to_atom[key]


    tuple_to_atom = dict()

    prog = pddl_to_prolog.PrologProgram()

    for fact in task.init:
        if isinstance(fact, pddl.Atom):
            for num, obj in enumerate(fact.args):
                if obj in objects and (fact.predicate, num) not in tuple_to_atom:
                    prog.add_fact(get_atom((fact.predicate, num)))

    for op in task.actions:
        condition = op.precondition
        param_to_body = compute_param_condition_to_rule_body(condition)

        # add rule for operator applicability
        for param in op.parameters:
            condition = [get_atom(x) for x in param_to_body[param.name]]
            rule = pddl_to_prolog.Rule(condition, get_atom((op, param.name)))
            prog.add_rule(rule)


        for eff in op.effects:
            condition = eff.condition
            eff_args = set(eff.literal.args)
            eff_arg_to_body = defaultdict(set)

            if isinstance(condition, pddl.Conjunction):
                for literal in condition.parts:
                    for index, param in enumerate(literal.args):
                        if param in eff_args:
                            eff_arg_to_body[param].add((literal.predicate, index))
            elif isinstance(condition, pddl.Literal):
                literal = condition
                for index, param in enumerate(literal.args):
                    if param in eff_args:
                        eff_arg_to_body[param].add((literal.predicate, index))
            elif isinstance(condition, pddl.Truth):
                pass
            else:
                assert False

            for index, param in enumerate(eff.literal.args):
                condition = []
                if param not in eff.parameters:
                    # param is action parameter
                    condition.append(get_atom((op, param)))
                for x in eff_arg_to_body[param]:
                    condition.append(get_atom(x))
                rule = pddl_to_prolog.Rule(condition,
                                           get_atom((eff.literal.predicate, index)))
                prog.add_rule(rule)

    for ax in task.axioms:
        condition = ax.condition
        param_to_body = compute_param_condition_to_rule_body(condition)

        # add rule for axiom applicability
        for param in ax.parameters:
            condition = [get_atom(x) for x in param_to_body[param.name]]
            rule = pddl_to_prolog.Rule(condition, get_atom((ax, param.name)))
            prog.add_rule(rule)



        relevant_args = set(ax.parameters[:ax.num_external_parameters])
        arg_to_body = defaultdict(set)

        if isinstance(condition, pddl.Conjunction):
            for literal in condition.parts:
                for index, param in enumerate(literal.args):
                    if param in relevant_args:
                        arg_to_body[param].add((literal.predicate, index))
        elif isinstance(condition, pddl.Literal):
            literal = condition
            for index, param in enumerate(literal.args):
                if param in relevant_args:
                    arg_to_body[param].add((literal.predicate, index))
        elif isinstance(condition, pddl.Truth):
            pass
        else:
            assert False


        for index, param in enumerate(ax.parameters[:ax.num_external_parameters]):
            condition = [get_atom(x) for x in arg_to_body[param]]
            rule = pddl_to_prolog.Rule(condition,
                                       get_atom((ax.name, index)))
            prog.add_rule(rule)

    prog.normalize()
    prog.split_rules()
    return prog


if __name__ == "__main__":
    import pddl_parser
    task = pddl_parser.open()
    normalize.normalize(task)
    objects = set(["obj43", "obj42", "obj41", "obj33", "obj32", "obj31",
                  "obj23", "obj22", "obj21", "obj13", "obj12", "obj11"])
    prog = build_reachability_program(task, objects)
    prog.dump()
    model = build_model.compute_model(prog)
    for atom in model:
        print(atom)
    print("%d atoms" % len(model))
