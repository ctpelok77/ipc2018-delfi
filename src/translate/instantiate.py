#! /usr/bin/env python

from __future__ import print_function

from collections import defaultdict, deque

import build_model
import itertools
import options
import pddl_to_prolog
import pddl
import reduction
import timers

def get_fluent_facts(task, model):
    fluent_predicates = set()
    for action in task.actions:
        for effect in action.effects:
            fluent_predicates.add(effect.literal.predicate)
    for axiom in task.axioms:
        fluent_predicates.add(axiom.name)
    return set([fact for fact in model
                if fact.predicate in fluent_predicates])

def get_objects_by_type(typed_objects, types):
    result = defaultdict(list)
    supertypes = {}
    for type in types:
        supertypes[type.name] = type.supertype_names
    for obj in typed_objects:
        result[obj.type_name].append(obj.name)
        for type in supertypes[obj.type_name]:
            result[type].append(obj.name)
    return result

def instantiate(task, model):
    relaxed_reachable = False
    fluent_facts = get_fluent_facts(task, model)
    init_facts = set(task.init)

    type_to_objects = get_objects_by_type(task.objects, task.types)

    instantiated_actions = []
    instantiated_axioms = []
    reachable_action_parameters = defaultdict(list)
    for atom in model:
        if isinstance(atom.predicate, pddl.Action):
            action = atom.predicate
            parameters = action.parameters
            inst_parameters = atom.args[:len(parameters)]
            # Note: It's important that we use the action object
            # itself as the key in reachable_action_parameters (rather
            # than action.name) since we can have multiple different
            # actions with the same name after normalization, and we
            # want to distinguish their instantiations.
            reachable_action_parameters[action].append(inst_parameters)
            variable_mapping = dict([(par.name, arg)
                                     for par, arg in zip(parameters, atom.args)])
            inst_action = action.instantiate(variable_mapping, init_facts,
                                             fluent_facts, type_to_objects,
                                             task.use_min_cost_metric)
            if inst_action:
                instantiated_actions.append(inst_action)
        elif isinstance(atom.predicate, pddl.Axiom):
            axiom = atom.predicate
            variable_mapping = dict([(par.name, arg)
                                     for par, arg in zip(axiom.parameters, atom.args)])
            inst_axiom = axiom.instantiate(variable_mapping, init_facts, fluent_facts)
            if inst_axiom:
                instantiated_axioms.append(inst_axiom)
        elif atom.predicate == "@goal-reachable":
            relaxed_reachable = True

    return (relaxed_reachable, fluent_facts, instantiated_actions,
            sorted(instantiated_axioms), reachable_action_parameters)

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

def explore(task, symmetric_object_sets = None):
    timer = timers.Timer()
    object_sets_and_preserved_subsets = reduction.compute_selected_object_sets_and_preserved_subsets(task, symmetric_object_sets)
    to_be_removed_objects = set()
    for obj_set, preserved_subset in object_sets_and_preserved_subsets:
        to_be_removed_objects |= (obj_set - preserved_subset)
    prog = pddl_to_prolog.translate(task, to_be_removed_objects)
    model = build_model.compute_model(prog)
    time = timer.elapsed_time()
    if options.expand_reduced_task:
        assert options.symmetry_reduced_grounding
        for symm_obj_set, subset in object_sets_and_preserved_subsets:
            expand(model, symm_obj_set)
    print ("Done building program and model: %ss" % time)
    with timers.timing("Completing instantiation"):
        return instantiate(task, model)

if __name__ == "__main__":
    import pddl_parser
    task = pddl_parser.open()
    relaxed_reachable, atoms, actions, axioms, _ = explore(task)
    print("goal relaxed reachable: %s" % relaxed_reachable)
    print("%d atoms:" % len(atoms))
    for atom in atoms:
        print(" ", atom)
    print()
    print("%d actions:" % len(actions))
    for action in actions:
        action.dump()
        print()
    print()
    print("%d axioms:" % len(axioms))
    for axiom in axioms:
        axiom.dump()
        print()
