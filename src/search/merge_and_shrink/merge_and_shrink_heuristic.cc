#include "merge_and_shrink_heuristic.h"

#include "factored_transition_system.h"
#include "fts_factory.h"
#include "labels.h"
#include "merge_strategy.h"
#include "shrink_strategy.h"
#include "transition_system.h"

#include "../option_parser.h"
#include "../plugin.h"
#include "../task_tools.h"
#include "../timer.h"
#include "../utilities.h"

#include <cassert>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

using namespace std;

MergeAndShrinkHeuristic::MergeAndShrinkHeuristic(const Options &opts)
    : Heuristic(opts),
      merge_strategy(opts.get<shared_ptr<MergeStrategy>>("merge_strategy")),
      shrink_strategy(opts.get<shared_ptr<ShrinkStrategy>>("shrink_strategy")),
      labels(opts.get<shared_ptr<Labels>>("label_reduction")),
      starting_peak_memory(-1),
      fts(nullptr) {
    /*
      TODO: Can we later get rid of the initialize calls, after rethinking
      how to handle communication between different components? See issue559.
    */
    merge_strategy->initialize(task);
    labels->initialize(task_proxy);
}

void MergeAndShrinkHeuristic::report_peak_memory_delta(bool final) const {
    if (final)
        cout << "Final";
    else
        cout << "Current";
    cout << " peak memory increase of merge-and-shrink computation: "
         << get_peak_memory_in_kb() - starting_peak_memory << " KB" << endl;
}

void MergeAndShrinkHeuristic::dump_options() const {
    merge_strategy->dump_options();
    shrink_strategy->dump_options();
    labels->dump_options();
}

void MergeAndShrinkHeuristic::warn_on_unusual_options() const {
    string dashes(79, '=');
    if (!labels->reduce_before_merging() && !labels->reduce_before_shrinking()) {
        cerr << dashes << endl
             << "WARNING! You did not enable label reduction. This may "
            "drastically reduce the performance of merge-and-shrink!"
             << endl << dashes << endl;
    } else if (labels->reduce_before_merging() && labels->reduce_before_shrinking()) {
        cerr << dashes << endl
             << "WARNING! You set label reduction to be applied twice in "
            "each merge-and-shrink iteration, both before shrinking and\n"
            "merging. This double computation effort does not pay off "
            "for most configurations!"
             << endl << dashes << endl;
    } else {
        if (labels->reduce_before_shrinking() &&
            (shrink_strategy->get_name() == "f-preserving"
             || shrink_strategy->get_name() == "random")) {
            cerr << dashes << endl
                 << "WARNING! Bucket-based shrink strategies such as "
                "f-preserving random perform best if used with label\n"
                "reduction before merging, not before shrinking!"
                 << endl << dashes << endl;
        }
        if (labels->reduce_before_merging() &&
            shrink_strategy->get_name() == "bisimulation") {
            cerr << dashes << endl
                 << "WARNING! Shrinking based on bisimulation performs best "
                "if used with label reduction before shrinking, not\n"
                "before merging!"
                 << endl << dashes << endl;
        }
    }
}

void MergeAndShrinkHeuristic::build_transition_system(const Timer &timer) {
    // TODO: We're leaking memory here in various ways. Fix this.
    //       Don't forget that build_atomic_transition_systems also
    //       allocates memory.

    fts = make_shared<FactoredTransitionSystem>(create_factored_transition_system(task_proxy, labels));
    cout << endl;

    int final_index = -1; // TODO: get rid of this
    if (fts->is_solvable()) { // All atomic transition system are solvable.
        while (!merge_strategy->done()) {
            // Choose next transition systems to merge
            pair<int, int> merge_indices = merge_strategy->get_next(fts);
            int merge_index1 = merge_indices.first;
            int merge_index2 = merge_indices.second;
            assert(merge_index1 != merge_index2);
            fts->statistics(merge_index1, timer);
            fts->statistics(merge_index2, timer);

            if (labels->reduce_before_shrinking()) {
                fts->label_reduction(merge_indices);
            }

            // Shrinking
            pair<bool, bool> shrunk = shrink_strategy->shrink(
                fts, merge_index1, merge_index2);
            if (shrunk.first)
                fts->statistics(merge_index1, timer);
            if (shrunk.second)
                fts->statistics(merge_index2, timer);

            if (labels->reduce_before_merging()) {
                fts->label_reduction(merge_indices);
            }

            // Merging
            final_index = fts->merge(task_proxy, merge_index1, merge_index2);
            fts->statistics(final_index, timer);

            /*
              NOTE: both the shrinking strategy classes and the construction of
              the composite require input transition systems to be solvable.
            */
            if (!fts->is_solvable()) {
                break;
            }

            report_peak_memory_delta();
            cout << endl;
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

    labels = nullptr;
}

void MergeAndShrinkHeuristic::initialize() {
    Timer timer;
    cout << "Initializing merge-and-shrink heuristic..." << endl;
    starting_peak_memory = get_peak_memory_in_kb();
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
        "paper:\n\n"
        " * Silvan Sievers, Martin Wehrle, and Malte Helmert.<<BR>>\n"
        " [Generalized Label Reduction for Merge-and-Shrink Heuristics "
        "http://ai.cs.unibas.ch/papers/sievers-et-al-aaai2014.pdf].<<BR>>\n "
        "In //Proceedings of the 28th AAAI Conference on Artificial "
        "Intelligence (AAAI 2014)//, pp. 2358-2366. AAAI Press 2014.\n"
        "For a more exhaustive description of merge-and-shrink, see the journal "
        "paper\n\n"
        " * Malte Helmert, Patrik Haslum, Joerg Hoffmann, and Raz Nissim.<<BR>>\n"
        " [Merge-and-Shrink Abstraction: A Method for Generating Lower Bounds "
        "in Factored State Spaces "
        "http://ai.cs.unibas.ch/papers/helmert-et-al-jacm2014.pdf].<<BR>>\n "
        "//Journal of the ACM 61 (3)//, pp. 16:1-63. 2014\n"
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
    parser.add_option<shared_ptr<Labels>>(
        "label_reduction",
        "See detailed documentation for labels. There is currently only "
        "one 'option' to use label_reduction. Also note the interaction "
        "with shrink strategies.");

    Heuristic::add_options_to_parser(parser);
    Options opts = parser.parse();

    if (parser.dry_run()) {
        return nullptr;
    } else {
        return new MergeAndShrinkHeuristic(opts);
    }
}

static Plugin<Heuristic> _plugin("merge_and_shrink", _parse);
