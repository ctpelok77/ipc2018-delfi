#! /usr/bin/env python

from collections import defaultdict

import build_model
import normalize
import pddl
import pddl_to_prolog


def build_reachability_program(task, objects):
    prog = pddl_to_prolog.PrologProgram()

    for fact in task.init:
        if isinstance(fact, pddl.Atom):
            for num, obj in enumerate(fact.args):
                if obj in objects:
                    prog.add_fact(pddl.Atom((fact.predicate, num), ()))

    for op in task.actions:
        op_param_to_body = defaultdict(set)
       
        if isinstance(op.precondition, pddl.Conjunction):
            for literal in op.precondition.parts:
                for index, param in enumerate(literal.args):
                    op_param_to_body[param].add((literal.predicate, index))
        elif isinstance(op.precondition, pddl.Literal):
            literal = op.precondition
            for index, param in enumerate(literal.args):
                op_param_to_body[param].add((literal.predicate, index))
        elif isinstance(op.condition, pddl.Truth):
            pass
        else:
            assert False

        # add rule for operator applicability
        for param, body in op_param_to_body.items():
            condition = [pddl.Atom(x, ()) for x in body]
            rule = pddl_to_prolog.Rule(condition, pddl.Atom((op, param), ()))
            prog.add_rule(rule)


        for eff in op.effects:
            eff_args = set(eff.literal.args)
            eff_arg_to_body = defaultdict(set)

            if isinstance(eff.condition, pddl.Conjunction):
                for literal in eff.condition.parts:
                    for index, param in enumerate(literal.args):
                        if param in eff_args:
                            eff_arg_to_body[param].add((literal.predicate, index))
            elif isinstance(eff.condition, pddl.Literal):
                literal = eff.condition
                for index, param in enumerate(literal.args):
                    if param in eff_args:
                        eff_arg_to_body[param].add((literal.predicate, index))
            elif isinstance(eff.condition, pddl.Truth):
                pass
            else:
                eff.condition.dump()
                assert False

            for index, param in enumerate(eff.literal.args):
                condition = []
                if param not in eff.parameters:
                    # param is action parameter
                    condition.append(pddl.Atom((op, param), ()))
                for x in eff_arg_to_body[param]:
                    condition.append(pddl.Atom(x, ()))
                rule = pddl_to_prolog.Rule(condition,
                                           pddl.Atom((eff.literal.predicate, index), ()))
                prog.add_rule(rule)

    for ax in task.axioms:
        relevant_args = set(ax.parameters[:ax.num_external_parameters])
        arg_to_body = defaultdict(set)

        if isinstance(ax.condition, pddl.Conjunction):
            for literal in ax.condition.parts:
                for index, param in enumerate(literal.args):
                    if param in relevant_args:
                        arg_to_body[param].add((literal.predicate, index))
        elif isinstance(ax.condition, pddl.Literal):
            literal = ax.condition
            for index, param in enumerate(literal.args):
                if param in relevant_args:
                    arg_to_body[param].add((literal.predicate, index))
        elif isinstance(ax.condition, pddl.Truth):
            pass
        else:
            assert False

        
        for index, param in enumerate(ax.parameters[:ax.num_external_parameters]):
            condition = [pddl.Atom(x, ()) for x in arg_to_body[param]]
            rule = pddl_to_prolog.Rule(condition,
                                       pddl.Atom((ax.name, index), ()))
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
