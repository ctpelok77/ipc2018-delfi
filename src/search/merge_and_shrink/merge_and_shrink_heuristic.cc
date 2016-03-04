#include "merge_and_shrink_heuristic.h"

#include "factored_transition_system.h"
#include "fts_factory.h"
#include "label_reduction.h"
#include "labels.h"
#include "merge_strategy.h"
#include "shrink_strategy.h"
#include "transition_system.h"

#include "../option_parser.h"
#include "../plugin.h"
#include "../task_tools.h"

#include "../utils/logging.h"
#include "../utils/markup.h"
#include "../utils/memory.h"
#include "../utils/system.h"
#include "../utils/timer.h"

#include <cassert>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

using namespace std;

namespace merge_and_shrink {
MergeAndShrinkHeuristic::MergeAndShrinkHeuristic(const Options &opts)
    : Heuristic(opts),
      merge_strategy(opts.get<shared_ptr<MergeStrategy>>("merge_strategy")),
      shrink_strategy(opts.get<shared_ptr<ShrinkStrategy>>("shrink_strategy")),
      label_reduction(nullptr),
      starting_peak_memory(-1),
      fts(nullptr) {
    /*
      TODO: Can we later get rid of the initialize calls, after rethinking
      how to handle communication between different components? See issue559.
    */
    merge_strategy->initialize(task);
    if (opts.contains("label_reduction")) {
        label_reduction = opts.get<shared_ptr<LabelReduction>>("label_reduction");
        label_reduction->initialize(task_proxy);
    }
}

void MergeAndShrinkHeuristic::report_peak_memory_delta(bool final) const {
    if (final)
        cout << "Final";
    else
        cout << "Current";
    cout << " peak memory increase of merge-and-shrink computation: "
         << utils::get_peak_memory_in_kb() - starting_peak_memory << " KB"
         << endl;
}

void MergeAndShrinkHeuristic::dump_options() const {
    merge_strategy->dump_options();
    shrink_strategy->dump_options();
    if (label_reduction) {
        label_reduction->dump_options();
    } else {
        cout << "Label reduction disabled" << endl;
    }
}

void MergeAndShrinkHeuristic::warn_on_unusual_options() const {
    string dashes(79, '=');
    if (!label_reduction) {
        cerr << dashes << endl
             << "WARNING! You did not enable label reduction. This may "
            "drastically reduce the performance of merge-and-shrink!"
             << endl << dashes << endl;
    } else if (label_reduction->reduce_before_merging() && label_reduction->reduce_before_shrinking()) {
        cerr << dashes << endl
             << "WARNING! You set label reduction to be applied twice in "
            "each merge-and-shrink iteration, both before shrinking and\n"
            "merging. This double computation effort does not pay off "
            "for most configurations!"
             << endl << dashes << endl;
    } else {
        if (label_reduction->reduce_before_shrinking() &&
            (shrink_strategy->get_name() == "f-preserving"
             || shrink_strategy->get_name() == "random")) {
            cerr << dashes << endl
                 << "WARNING! Bucket-based shrink strategies such as "
                "f-preserving random perform best if used with label\n"
                "reduction before merging, not before shrinking!"
                 << endl << dashes << endl;
        }
        if (label_reduction->reduce_before_merging() &&
            shrink_strategy->get_name() == "bisimulation") {
            cerr << dashes << endl
                 << "WARNING! Shrinking based on bisimulation performs best "
                "if used with label reduction before shrinking, not\n"
                "before merging!"
                 << endl << dashes << endl;
        }
    }
}

void MergeAndShrinkHeuristic::build_transition_system(const utils::Timer &timer) {
    // TODO: We're leaking memory here in various ways. Fix this.
    //       Don't forget that build_atomic_transition_systems also
    //       allocates memory.

    fts = utils::make_unique_ptr<FactoredTransitionSystem>(
        create_factored_transition_system(task_proxy));
    cout << endl;
    int maximum_intermediate_size = 0;
    for (int i = 0; i < fts->get_size(); ++i) {
        int size = fts->get_ts(i).get_size();
        if (size > maximum_intermediate_size) {
            maximum_intermediate_size = size;
        }
    }

    vector<int> init_hvalue_increase;
    vector<int> remaining_labels;
    remaining_labels.push_back(fts->get_labels().compute_number_active_labels());
    int iteration_counter = 0;
    bool still_perfect = true;
    vector<pair<int, int>> merge_order;
    int final_index = -1; // TODO: get rid of this
    if (fts->is_solvable()) { // All atomic transition system are solvable.
        while (!merge_strategy->done()) {
            // Choose next transition systems to merge
            pair<int, int> merge_indices = merge_strategy->get_next(*fts);
            int merge_index1 = merge_indices.first;
            int merge_index2 = merge_indices.second;
            cout << "Next pair of indices: (" << merge_index1 << ", " << merge_index2 << ")" << endl;
            assert(merge_index1 != merge_index2);
            merge_order.push_back(merge_indices);
            fts->statistics(merge_index1, timer);
            fts->statistics(merge_index2, timer);

            if (label_reduction && label_reduction->reduce_before_shrinking()) {
                label_reduction->reduce(merge_indices, *fts);
                remaining_labels.push_back(fts->get_labels().compute_number_active_labels());
            }

            // Shrinking
            pair<bool, bool> shrunk = shrink_strategy->shrink(
                *fts, merge_index1, merge_index2);
            if (shrunk.first)
                fts->statistics(merge_index1, timer);
            if (shrunk.second)
                fts->statistics(merge_index2, timer);

            const vector<double> &miss_qualified_states_ratios =
                shrink_strategy->get_miss_qualified_states_ratios();
            int size = miss_qualified_states_ratios.size();
            if (size >= 2 && still_perfect &&
                (miss_qualified_states_ratios[size - 1]
                 || miss_qualified_states_ratios[size - 2])) {
                // The test for size >= 2 is to ensure we actually record
                // this kind of statistics -- currently only with bisimulation
                // shrinking.
                cout << "not perfect anymore in iteration " << iteration_counter << endl;
                still_perfect = false;
            }

            if (label_reduction && label_reduction->reduce_before_merging()) {
                label_reduction->reduce(merge_indices, *fts);
                remaining_labels.push_back(fts->get_labels().compute_number_active_labels());
            }

            int init_dist1 = fts->get_init_state_goal_distance(merge_index1);
            int init_dist2 = fts->get_init_state_goal_distance(merge_index2);

            // Merging
            final_index = fts->merge(merge_index1, merge_index2);
            int abs_size = fts->get_ts(final_index).get_size();
            if (abs_size > maximum_intermediate_size) {
                maximum_intermediate_size = abs_size;
            }
            /*
              NOTE: both the shrinking strategy classes and the construction of
              the composite require input transition systems to be solvable.
            */
            if (!fts->is_solvable()) {
                break;
            }

            fts->statistics(final_index, timer);

            int new_init_dist = fts->get_init_state_goal_distance(final_index);
            int difference = new_init_dist - max(init_dist1, init_dist2);
            cout << "Difference of init h values: " << difference << endl;
            init_hvalue_increase.push_back(difference);

            report_peak_memory_delta();
            cout << endl;
            ++iteration_counter;
        }
    }

    if (fts->is_solvable()) {
        cout << "Final transition system size: "
             << fts->get_ts(final_index).get_size() << endl;
        // need to finalize before calling "get_cost"
        fts->finalize();
        // TODO: after adopting the task interface everywhere, change this
        // back to compute_heuristic(task_proxy.get_initial_state())
        cout << "initial h value: "
             << fts->get_cost(task_proxy.get_initial_state())
             << endl;
    } else {
        cout << "Abstract problem is unsolvable!" << endl;
    }

    cout << "Maximum intermediate abstraction size: "
         << maximum_intermediate_size << endl;
    cout << "Init h value improvements: " << init_hvalue_increase << endl;
    cout << "Course of label reduction: " << remaining_labels << endl;
    const vector<double> &miss_qualified_states_ratios =
        shrink_strategy->get_miss_qualified_states_ratios();
    cout << "Course of miss qualified states shrinking: "
         << miss_qualified_states_ratios << endl;
    double summed_values = 0;
    for (double value : miss_qualified_states_ratios) {
        summed_values += value;
    }
    size_t number_of_shrinks = miss_qualified_states_ratios.size();
    double average_imperfect_shrinking = 0;
    if (number_of_shrinks) {
        average_imperfect_shrinking = summed_values / static_cast<double>(number_of_shrinks);
    }
    cout << "Average imperfect shrinking: " << average_imperfect_shrinking << endl;
    cout << "Merge order: [";
    bool linear_order = true;
    int next_index = task_proxy.get_variables().size();
    for (size_t i = 0; i < merge_order.size(); ++i) {
        pair<int, int> merge = merge_order[i];
        cout << "(" << merge.first << ", " << merge.second << ")";
        if (i != merge_order.size() - 1) {
            cout << ", ";
        }
        if (linear_order && i != 0) {
            if (merge.first != next_index && merge.second != next_index) {
                linear_order = false;
            }
            ++next_index;
        }
    }
    cout << "]" << endl;
    if (linear_order) {
        cout << "Linear merge order" << endl;
    } else {
         cout << "Non-linear merge order" << endl;
    }
    const vector<double> &pruning_statistics = fts->get_pruning_statistics();
    cout << "Relative pruning per iteration: " << pruning_statistics << endl;
    double summed_pruning = 0;
    for (double pruning : pruning_statistics) {
        summed_pruning += pruning;
    }
    // If pruning statistics are empty, then because the instance is unsolvable.
    // In this case, we return 0, which is the worst value possible for pruning.
    double average_pruning = 0;
    if (!pruning_statistics.empty()) {
        average_pruning =  summed_pruning / static_cast<double>(pruning_statistics.size());
    }
    cout << "Average relative pruning: " << average_pruning << endl;
    cout << "Iterations with merge tiebreaking: "
         << merge_strategy->get_iterations_with_tiebreaking() << endl;
    cout << "Total tiebreaking merge candidates: "
         << merge_strategy->get_total_tiebreaking_pair_count() << endl;

    merge_strategy = nullptr;
    shrink_strategy = nullptr;
    label_reduction = nullptr;
}

void MergeAndShrinkHeuristic::initialize() {
    utils::Timer timer;
    cout << "Initializing merge-and-shrink heuristic..." << endl;
    starting_peak_memory = utils::get_peak_memory_in_kb();
    verify_no_axioms(task_proxy);
    dump_options();
    warn_on_unusual_options();
    cout << endl;

    build_transition_system(timer);
    report_peak_memory_delta(true);
    cout << "Done initializing merge-and-shrink heuristic [" << timer << "]"
         << endl;
    cout << endl;
}

int MergeAndShrinkHeuristic::compute_heuristic(const GlobalState &global_state) {
    State state = convert_global_state(global_state);
    int cost = fts->get_cost(state);
    if (cost == -1)
        return DEAD_END;
    return cost;
}

static Heuristic *_parse(OptionParser &parser) {
    parser.document_synopsis(
        "Merge-and-shrink heuristic",
        "This heuristic implements the algorithm described in the following "
        "paper:" + utils::format_paper_reference(
            {"Silvan Sievers", "Martin Wehrle", "Malte Helmert"},
            "Generalized Label Reduction for Merge-and-Shrink Heuristics",
            "http://ai.cs.unibas.ch/papers/sievers-et-al-aaai2014.pdf",
            "Proceedings of the 28th AAAI Conference on Artificial"
            " Intelligence (AAAI 2014)",
            "2358-2366",
            "AAAI Press 2014") + "\n" +
        "For a more exhaustive description of merge-and-shrink, see the journal "
        "paper" + utils::format_paper_reference(
            {"Malte Helmert", "Patrik Haslum", "Joerg Hoffmann", "Raz Nissim"},
            "Merge-and-Shrink Abstraction: A Method for Generating Lower Bounds"
            " in Factored State Spaces",
            "http://ai.cs.unibas.ch/papers/helmert-et-al-jacm2014.pdf",
            "Journal of the ACM 61 (3)",
            "16:1-63",
            "2014") + "\n" +
        "Please note that the journal paper describes the \"old\" theory of "
        "label reduction, which has been superseded by the above conference "
        "paper and is no longer implemented in Fast Downward.");
    parser.document_language_support("action costs", "supported");
    parser.document_language_support("conditional effects", "supported (but see note)");
    parser.document_language_support("axioms", "not supported");
    parser.document_property("admissible", "yes");
    parser.document_property("consistent", "yes");
    parser.document_property("safe", "yes");
    parser.document_property("preferred operators", "no");
    parser.document_note(
        "Note",
        "Conditional effects are supported directly. Note, however, that "
        "for tasks that are not factored (in the sense of the JACM 2014 "
        "merge-and-shrink paper), the atomic transition systems on which "
        "merge-and-shrink heuristics are based are nondeterministic, "
        "which can lead to poor heuristics even when only perfect shrinking "
        "is performed.");
    parser.document_note(
        "Note",
        "A currently recommended good configuration uses bisimulation "
        "based shrinking (selecting max states from 50000 to 200000 is "
        "reasonable), DFP merging, and the appropriate label "
        "reduction setting:\n"
        "merge_and_shrink(shrink_strategy=shrink_bisimulation(max_states=100000,"
        "threshold=1,greedy=false),merge_strategy=merge_dfp(),"
        "label_reduction=label_reduction(before_shrinking=true, before_merging=false))");

    // Merge strategy option.
    parser.add_option<shared_ptr<MergeStrategy>>(
        "merge_strategy",
        "See detailed documentation for merge strategies. "
        "We currently recommend merge_dfp.");

    // Shrink strategy option.
    parser.add_option<shared_ptr<ShrinkStrategy>>(
        "shrink_strategy",
        "See detailed documentation for shrink strategies. "
        "We currently recommend shrink_bisimulation.");

    // Label reduction option.
    parser.add_option<shared_ptr<LabelReduction>>(
        "label_reduction",
        "See detailed documentation for labels. There is currently only "
        "one 'option' to use label_reduction. Also note the interaction "
        "with shrink strategies.",
        OptionParser::NONE);

    Heuristic::add_options_to_parser(parser);
    Options opts = parser.parse();

    if (parser.dry_run()) {
        return nullptr;
    } else {
        return new MergeAndShrinkHeuristic(opts);
    }
}

static Plugin<Heuristic> _plugin("merge_and_shrink", _parse);
}
