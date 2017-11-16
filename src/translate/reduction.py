#! /usr/bin/env python

from collections import defaultdict, deque

import build_model
import itertools
import normalize
import options
import pddl
import pddl_to_prolog
import timers

def add_prog_atom_for_pddl_atom(atom, param_to_body, params):
    for index, param in enumerate(atom.args):
        if params is None or param in params:
            param_to_body[param].add((atom.predicate, index))

def compute_param_condition_to_rule_body(condition, params=None):
    param_to_body = defaultdict(set)

    if isinstance(condition, pddl.Conjunction):
        for literal in condition.parts:
            if isinstance(literal, pddl.Atom): # Ignore negative atoms
                add_prog_atom_for_pddl_atom(literal, param_to_body, params)
    elif isinstance(condition, pddl.Literal):
        if isinstance(condition, pddl.Atom): # Ignore negative atoms
            add_prog_atom_for_pddl_atom(condition, param_to_body, params)
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

        # add rules for operator effects
        for eff in op.effects:
            condition = eff.condition
            eff_args = set(eff.literal.args)
            eff_arg_to_body = compute_param_condition_to_rule_body(condition, eff_args)

            for index, param in enumerate(eff.literal.args):
                condition = []
                if param not in [param.name for param in eff.parameters]:
                    # param is action parameter
                    condition.append(get_atom((op, param)))
                for x in eff_arg_to_body[param]:
                    condition.append(get_atom(x))
                rule = pddl_to_prolog.Rule(condition,
                                           get_atom((eff.literal.predicate, index)))
                prog.add_rule(rule)

    for ax in task.axioms:
        # add rule for axiom applicability
        condition = ax.condition
        param_to_body = compute_param_condition_to_rule_body(condition)
        for param in ax.parameters:
            condition = [get_atom(x) for x in param_to_body[param.name]]
            rule = pddl_to_prolog.Rule(condition, get_atom((ax, param.name)))
            prog.add_rule(rule)


        # add rules for axiom head
        condition = ax.condition
        relevant_args = set(ax.parameters[:ax.num_external_parameters])
        arg_to_body = compute_param_condition_to_rule_body(condition, relevant_args)
        for index, param in enumerate(ax.parameters[:ax.num_external_parameters]):
            condition = [get_atom(x) for x in arg_to_body[param]]
            rule = pddl_to_prolog.Rule(condition,
                                       get_atom((ax.name, index)))
            prog.add_rule(rule)

    prog.normalize()
    prog.split_rules()
    return prog


def compute_parameter_reachability(task, object_set):
    #task.dump()
    prog = build_reachability_program(task, object_set)
    #prog.dump()
    model = build_model.compute_model(prog)
    return model


def compute_max_predicate_arity_simple(predicates):
    max_arity = 0
    for pred in predicates:
        max_arity = max(max_arity, len(pred.arguments))
    return max_arity


def compute_max_predicate_arity_tight(predicates, model):
    max_arity = 0
    for pred in predicates:
        param_indices_instantiable_with_objects_from_set = set()
        for atom in model:
            key_index = atom.predicate
            if key_index[0] == pred.name:
                param_indices_instantiable_with_objects_from_set.add(key_index[1])
        assert len(param_indices_instantiable_with_objects_from_set) <= len(pred.arguments)
        max_arity = max(max_arity, len(param_indices_instantiable_with_objects_from_set))
    return max_arity


def compute_num_occurring_objects_from_set_in_op(op, object_set):
    occurring_objects = op.precondition.get_constants()
    for effect in op.effects:
        occurring_objects |= effect.condition.get_constants()
        occurring_objects |= effect.literal.get_constants()
    num_obj_from_symm_obj_set = len(occurring_objects & object_set)
    return num_obj_from_symm_obj_set


def compute_max_operator_arity_simple(operators, object_set):
    max_arity = 0
    for op in operators:
        num_params = len(op.parameters)
        num_obj_from_symm_obj_set = compute_num_occurring_objects_from_set_in_op(op, object_set)
        op_arity = num_params + num_obj_from_symm_obj_set
        max_arity = max(max_arity, op_arity)
    return max_arity


def compute_max_operator_arity_tight(operators, model, object_set):
    max_arity = 0
    for op in operators:
        params_instantiatable_with_objects_from_set = set()
        for atom in model:
            key_index = atom.predicate
            if isinstance(key_index[0], pddl.Action) and key_index[0] is op:
                assert key_index[1] in [param.name for param in op.parameters]
                params_instantiatable_with_objects_from_set.add(key_index[1])
        param_arity = len(params_instantiatable_with_objects_from_set)

        num_obj_from_symm_obj_set = compute_num_occurring_objects_from_set_in_op(op, object_set)

        op_arity = param_arity + num_obj_from_symm_obj_set
        max_arity = max(max_arity, op_arity)
    return max_arity


def compute_num_occurring_objects_from_set_in_ax(ax, object_set):
    occurring_objects = ax.condition.get_constants()
    # TODO: can objects occur in the head of an axiom?
    num_obj_from_symm_obj_set = len(occurring_objects & object_set)
    return num_obj_from_symm_obj_set


def compute_max_axiom_arity_simple(axioms, object_set):
    max_arity = 0
    for ax in axioms:
        num_params = len(ax.parameters)
        num_obj_from_symm_obj_set = compute_num_occurring_objects_from_set_in_ax(ax, object_set)
        ax_arity = num_params + num_obj_from_symm_obj_set
        max_arity = max(max_arity, ax_arity)
    return max_arity


def compute_max_axiom_arity_tight(axioms, model, object_set):
    max_arity = 0
    for ax in axioms:
        params_instantiatable_with_objects_from_set = set()
        for atom in model:
            key_index = atom.predicate
            if isinstance(key_index[0], pddl.Axiom) and key_index[0] is ax:
                assert key_index[1] in [param.name for param in ax.parameters]
                params_instantiatable_with_objects_from_set.add(key_index[1])
        param_arity = len(params_instantiatable_with_objects_from_set)

        num_obj_from_symm_obj_set = compute_num_occurring_objects_from_set_in_ax(ax, object_set)

        ax_arity = param_arity + num_obj_from_symm_obj_set
        max_arity = max(max_arity, ax_arity)
    return max_arity


def compute_selected_object_sets_and_preserved_subsets(task, symmetric_object_sets):
    result = []
    if symmetric_object_sets is not None:
        assert options.symmetry_reduced_grounding or options.symmetry_reduced_grounding_for_h2_mutexes
        bounds_timer = timers.Timer()
        for symm_obj_set in symmetric_object_sets:
            if len(symm_obj_set) <= 2:
                # due to =-predicates, we can skip all singleton and pair symmetric object sets
                continue
            print("Consider symmetric object set:")
            print(", ".join([x for x in symm_obj_set]))

            model = compute_parameter_reachability(task, symm_obj_set)
            max_pred_arity_tight = compute_max_predicate_arity_tight(task.predicates, model)
            print("Maximum predicate arity given symmetric object set tight: {}".format(max_pred_arity_tight))
            max_op_arity_tight = compute_max_operator_arity_tight(task.actions, model, symm_obj_set)
            print("Maximum operator arity given symmetric object set tight: {}".format(max_op_arity_tight))
            max_ax_arity_tight = compute_max_axiom_arity_tight(task.axioms, model, symm_obj_set)
            print("Maximum axiom arity given symmetric object set tight: {}".format(max_ax_arity_tight))
            max_arity = max(max_pred_arity_tight, max_op_arity_tight, max_ax_arity_tight)

            if options.symmetry_reduced_grounding_for_h2_mutexes:
                max_arity += max_pred_arity_tight
            print("Minimum object set size: {}".format(max_arity))

            if len(symm_obj_set) > max_arity:
                to_be_preserved_objects = set()
                for obj in symm_obj_set:
                    to_be_preserved_objects.add(obj)
                    if len(to_be_preserved_objects) == max_arity:
                        break
                print("Choosing subset of symmetric object set:")
                print(", ".join([x for x in to_be_preserved_objects]))
                result.append((symm_obj_set, to_be_preserved_objects))
            else:
                print("Not large enough")
        if result:
            print("Actually can perform a symmetry reduction")
        print("Total time to compute bounds and determine subsets of symmetric object sets: {}s".format(bounds_timer.elapsed_time()))
    print("Number of symmetric object sets used for symmetry reduction: {}".format(len(result)))
    return result


def permute_atom(atom, permutation):
    """Compute a symmetric atom from the given one and the given permutation."""
    symmetric_args = []
    for arg in atom.args:
        if arg in permutation:
            symmetric_args.append(permutation[arg])
        else:
            symmetric_args.append(arg)
    symmetric_atom = pddl.Atom(atom.predicate, symmetric_args)
    return symmetric_atom


def expand(model, symmetric_object_set):
    """Extend the model by all symmetric atoms, using all permutations created
    from the objects in *symmetric_object_set*."""
    print("Expanding model for symmetric object set:")
    print(", ".join([x for x in symmetric_object_set]))
    canonical_perm = tuple(symmetric_object_set)
    permutation_dicts = []
    for perm in itertools.permutations(symmetric_object_set):
        if perm != canonical_perm: # skip the one identity permutation
            permutation_dicts.append(dict(zip(canonical_perm, perm)))
    open_list = deque()
    closed_list = set()
    for atom in model:
        open_list.append(atom)
        closed_list.add(atom)
    while len(open_list):
        atom = open_list.popleft()
        for perm in permutation_dicts:
            symmetric_atom = permute_atom(atom, perm)
            if not symmetric_atom in closed_list:
                closed_list.add(symmetric_atom)
                model.append(symmetric_atom)
                open_list.append(symmetric_atom)


def assert_equal_grounding(relaxed_reachable, atoms, actions, axioms,
    reachable_action_params, relaxed_reachable2, atoms2, actions2, axioms2,
    reachable_action_params2):
    assert relaxed_reachable == relaxed_reachable2

    def equal_literals(lit1, lit2):
        return lit1.predicate == lit2.predicate and lit1.args == lit2.args

    for atom in atoms:
        found_atom = False
        for atom2 in atoms2:
            if equal_literals(atom, atom2):
                found_atom = True
                break
        assert found_atom

    def equal_conditions(conditions1, conditions2):
        for cond1 in conditions1:
            found_cond = False
            for cond2 in conditions2:
                if equal_literals(cond1, cond2):
                    found_cond = True
                    break
            if not found_cond:
                return False
        return True

    def equal_add_del_effects(effects1, effects2):
        for eff1 in effects1:
            found_eff = False
            for eff2 in effects2:
                assert len(eff1) == 2 and len(eff2) == 2
                if equal_conditions(eff1[0], eff2[0]) and equal_literals(eff1[1], eff2[1]):
                    found_eff = True
                    break
            if not found_eff:
                return False
        return True

    def equal_prop_actions(action1, action2):
        if action1.name != action2.name:
            return False
        if not equal_conditions(action1.precondition, action2.precondition):
            return False
        if not equal_add_del_effects(action1.add_effects, action2.add_effects):
            return False
        if not equal_add_del_effects(action1.del_effects, action2.del_effects):
            return False
        return action1.cost == action2.cost

    for action in actions:
        found_action = False
        for action2 in actions2:
            if equal_prop_actions(action, action2):
                found_action = True
                break
        assert found_action

    def equal_prop_axioms(axiom1, axiom2):
        if axiom1.name != axiom2.name:
            return False
        if not equal_conditions(axiom1.condition, axiom2.condition):
            return False
        return equal_literals(axiom1.effect, axiom2.effect)

    for axiom in axioms:
        found_axiom = False
        for axiom2 in axioms2:
            if equal_prop_axioms(axiom, axiom2):
                found_axiom = True
                break
        assert found_axiom

    def equal_lists_of_comparable_elements(list1, list2):
        for elem1 in list1:
            found_elem = False
            for elem2 in list2:
                if elem1 == elem2:
                    found_elem = True
                    break
            if not found_elem:
                return False
        return True

    def equal_actions(action1, action2):
        if action1.name != action2.name:
            return False
        if not equal_lists_of_comparable_elements(action1.parameters, action2.parameters):
            return False
        if action1.num_external_parameters != action2.num_external_parameters:
            return False
        if action1.precondition != action2.precondition:
            return False
        if not equal_lists_of_comparable_elements(action1.effects, action2.effects):
            return False
        if action1.cost != action2.cost:
            return False
        return action1.cost == action2.cost

    def equal_param_lists(params1, params2):
        for param1 in params1:
            found_param = False
            for param2 in params2:
                if param1 == param2:
                    found_param = True
                    break
            if not found_param:
                return False
        return True

    for action, params in reachable_action_params.items():
        found_reachable_action_param = False
        for action2 in reachable_action_params2.keys():
            if equal_actions(action, action2):
                params2 = reachable_action_params2[action2]
                if equal_param_lists(params, params2):
                    found_reachable_action_param = True
                    break
        assert found_reachable_action_param


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
