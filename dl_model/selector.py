#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
stderr = sys.stderr
sys.stderr = open('/dev/null', 'w')
from keras.models import model_from_json
sys.stderr = stderr

import numpy as np
from PIL import Image
import sys, os

ALGORITHM_TO_COMMAND_LINE_STRING = {
    'h2-simpless-dks-blind': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(blind,symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-dks-celmcut': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(celmcut,symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-dks-lmcountlmrhw': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(lmcount(lm_factory=lm_rhw,admissible=true,transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000,mpd=true)'],
    'h2-simpless-dks-lmcountlmmergedlmrhwlmhm1': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(lmcount(lm_factory=lm_merged([lm_rhw,lm_hm(m=1)]),admissible=true,transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000,mpd=true)'],
    'h2-simpless-dks-masb50ksccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=reverse_level,product_ts_order=new_to_old)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-dks-masb50ksbmiasm': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_stateless(merge_selector=score_based_filtering(scoring_functions=[sf_miasm(shrink_strategy=shrink_bisimulation,max_states=50000),total_order(atomic_before_product=true,atomic_ts_order=reverse_level,product_ts_order=old_to_new)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    # we do not use h2 with miasm on purpose, because it suffers a lot from missing "left-over mutexes"
    'simpless-dks-masb50kmiasmdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_precomputed(merge_tree=miasm(abstraction=miasm_merge_and_shrink(),fallback_merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_ts_order=reverse_level,product_ts_order=new_to_old,atomic_before_product=false)]))),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-dks-masginfsccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=true),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=level,product_ts_order=random)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=infinity,threshold_before_merge=1),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-dks-cpdbshc900': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(cpdbs(patterns=hillclimbing(max_time=900),transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-dks-zopdbsgenetic': ['--symmetries', 'sym=structural_symmetries(search_symmetries=dks)', '--search', 'astar(zopdbs(patterns=genetic(pdb_max_size=50000,num_collections=5,num_episodes=30,mutation_probability=0.01),transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-oss-blind': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(blind,symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-oss-celmcut': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(celmcut,symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-oss-lmcountlmrhw': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(lmcount(lm_factory=lm_rhw,admissible=true,transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000,mpd=true)'],
    'h2-simpless-oss-lmcountlmmergedlmrhwlmhm1': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(lmcount(lm_factory=lm_merged([lm_rhw,lm_hm(m=1)]),admissible=true,transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000,mpd=true)'],
    'h2-simpless-oss-masb50ksccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=reverse_level,product_ts_order=new_to_old)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-oss-masb50ksbmiasm': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_stateless(merge_selector=score_based_filtering(scoring_functions=[sf_miasm(shrink_strategy=shrink_bisimulation,max_states=50000),total_order(atomic_before_product=true,atomic_ts_order=reverse_level,product_ts_order=old_to_new)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    # we do not use h2 with miasm on purpose, because it suffers a lot from missing "left-over mutexes"
    'simpless-oss-masb50kmiasmdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),merge_strategy=merge_precomputed(merge_tree=miasm(abstraction=miasm_merge_and_shrink(),fallback_merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_ts_order=reverse_level,product_ts_order=new_to_old,atomic_before_product=false)]))),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=50000,threshold_before_merge=1,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-oss-masginfsccdfp': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=true),merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector=score_based_filtering(scoring_functions=[goal_relevance,dfp,total_order(atomic_before_product=false,atomic_ts_order=level,product_ts_order=random)])),label_reduction=exact(before_shrinking=true,before_merging=false),max_states=infinity,threshold_before_merge=1,prune_unreachable_states=false),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-oss-cpdbshc900': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(cpdbs(patterns=hillclimbing(max_time=900),transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'h2-simpless-oss-zopdbsgenetic': ['--symmetries', 'sym=structural_symmetries(search_symmetries=oss)', '--search', 'astar(zopdbs(patterns=genetic(pdb_max_size=50000,num_collections=5,num_episodes=30,mutation_probability=0.01),transform=multiply_out_conditional_effects),symmetries=sym,pruning=stubborn_sets_simple(minimum_pruning_ratio=0.01),num_por_probes=1000)'],
    'seq-opt-symba-1' : ['seq-opt-symba-1']
}

def compute_command_line_options():

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    # load json and create model
    json_file = open(os.path.join(sys.path[0],'model.json'), 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    model = model_from_json(loaded_model_json)
    # load weights into new model
    model.load_weights(os.path.join(sys.path[0],"model.h5"))
    #print("Loaded model from disk")

    list_solver_names = ['31d1eefdbeca-h2-simpless-dks-lmcountlmmergedlmrhwlmhm1', '31d1eefdbeca-h2-simpless-dks-masb50ksccdfp', '31d1eefdbeca-h2-simpless-dks-lmcountlmrhw', '31d1eefdbeca-h2-simpless-dks-blind', '31d1eefdbeca-h2-simpless-dks-celmcut', '31d1eefdbeca-h2-simpless-dks-zopdbsgenetic', '31d1eefdbeca-h2-simpless-dks-masb50ksbmiasm', '31d1eefdbeca-h2-simpless-dks-masginfsccdfp', '31d1eefdbeca-simpless-dks-masb50kmiasmdfp', '31d1eefdbeca-h2-simpless-dks-cpdbshc900', '31d1eefdbeca-h2-simpless-oss-blind', '31d1eefdbeca-h2-simpless-oss-celmcut', '31d1eefdbeca-h2-simpless-oss-lmcountlmrhw', '31d1eefdbeca-h2-simpless-oss-masb50ksccdfp', '31d1eefdbeca-h2-simpless-oss-lmcountlmmergedlmrhwlmhm1', '31d1eefdbeca-h2-simpless-oss-zopdbsgenetic', '31d1eefdbeca-h2-simpless-oss-cpdbshc900', '31d1eefdbeca-simpless-oss-masb50kmiasmdfp', '31d1eefdbeca-h2-simpless-oss-masb50ksbmiasm', '31d1eefdbeca-h2-simpless-oss-masginfsccdfp', 'seq-opt-symba-1']

    #print(str(len(list_solver_names)) + " Solvers: ")
    #print(list_solver_names)

    list_x = []

    img = Image.open(sys.argv[1])
    list_x.append(np.array(img))

    #print("\nNumber of total data points: " + str(len(list_x)))
    # Normalize feature image values to 0..1 range (assumes gray scale)
    data = np.array(list_x, dtype="float") / 255.0
    data  = data.reshape( data.shape[0], 128, 128, 1 )

    # For each test data point compute predictions for each of the solvers
    preds = model.predict(data)
    #print(preds)
    print(list_solver_names[np.argmax(preds[0])])

    selected_algorithm = 'seq-opt-symba-1'
    return ALGORITHM_TO_COMMAND_LINE_STRING[selected_algorithm]
