#include "merge_symmetries.h"

#include "symmetries/symmetries.h"

#include "../plugin.h"

#include <limits>

using namespace std;

MergeSymmetries::MergeSymmetries(const Options &options_)
    : MergeDFP(),
      options(options_),
      max_iterations(options.get<int>("max_iterations")),
      started_merging_cycle(false),
      number_of_applied_symmetries(0),
      iteration_counter(0) {
}

pair<int, int> MergeSymmetries::get_next(vector<Abstraction *> &all_abstractions) {
    assert(!done());
    ++iteration_counter;

    if (iteration_counter <= max_iterations && abs_to_merge.empty()) {
        Symmetries symmetries(options);
        pair<int, int> stats = symmetries.find_and_apply_symmetries(all_abstractions, abs_to_merge);
        number_of_applied_symmetries += stats.first;
        remaining_merges -= stats.second;
        cout << "Number of applied symmetries: " << number_of_applied_symmetries << endl;
        if (abs_to_merge.size() == 1 && abs_to_merge[0].size() == 1) {
            cerr << "Got one abstraction to merge!" << endl;
            exit_with(EXIT_CRITICAL_ERROR);
        } else if (!abs_to_merge.empty()) {
            cout << "Merging next: ";
            for (vector<vector<int> >::iterator it = abs_to_merge.begin(); it != abs_to_merge.end(); ++it) {
                cout << *it << " ";
            }
            cout << endl;
            // reset
            started_merging_cycle = false;
        }
    }

    if (abs_to_merge.empty()) {
        return MergeDFP::get_next(all_abstractions);
    }

    int first;
    if (!started_merging_cycle) {
        assert(abs_to_merge[0].size() > 1);
        started_merging_cycle = true;
        first = *abs_to_merge[0].begin();
        abs_to_merge[0].erase(abs_to_merge[0].begin());
    } else {
        first = all_abstractions.size() - 1;
    }
    assert(!abs_to_merge[0].empty());
    int second = *abs_to_merge[0].begin();
    abs_to_merge[0].erase(abs_to_merge[0].begin());
    if (abs_to_merge[0].empty()) {
        abs_to_merge.erase(abs_to_merge.begin());
        started_merging_cycle = false;
    }

    --remaining_merges;
    return make_pair(first, second);
}

string MergeSymmetries::name() const {
    return "symmetries";
}

static MergeStrategy *_parse(OptionParser &parser) {
    parser.add_option<bool>("debug_graph_creator", "produce dot readable output "
                            "from the graph generating methods", "false");
    parser.add_option<int>("max_iterations", "number of merge-and-shrink "
                           "iterations up to which symmetries should be computed."
                           "infinity");
    vector<string> symmetries_for_shrinking;
    symmetries_for_shrinking.push_back("ATOMIC");
    symmetries_for_shrinking.push_back("LOCAL");
    symmetries_for_shrinking.push_back("NONE");
    parser.add_enum_option("symmetries_for_shrinking",
                           symmetries_for_shrinking,
                           "choose the type of symmetries used for shrinking: "
                           "only atomic symmetries, "
                           "local symmetries, "
                           "only use for merging, no shrinking.",
                           "ATOMIC");
    vector<string> symmetries_for_merging;
    symmetries_for_merging.push_back("SMALLEST");
    symmetries_for_merging.push_back("LARGEST");
    symmetries_for_merging.push_back("ZERO");
    parser.add_enum_option("symmetries_for_merging",
                           symmetries_for_merging,
                           "choose the type of symmetries used for merging: "
                           "the smallest or the largest in number of abstractions "
                           "that are affected (atomic shrinking or no shrinking) "
                           "or mapped (local shrinking).",
                           "SMALLEST");
    vector<string> internal_merging;
    internal_merging.push_back("LINEAR");
    internal_merging.push_back("NON_LINEAR");
    parser.add_enum_option("internal_merging",
                           internal_merging,
                           "choose how the set of abstractions that must be "
                           "merged for symmetries is merged: "
                           "linearly, resulting in one large abstractions, "
                           "non linearly, resulting in one composite abstraction "
                           "for every previous cycle of the chosen symmetry.",
                           "LINEAR");
    parser.add_option<bool>("build_stabilized_pdg", "build an abstraction "
                            "stabilized pdb, which results in bliss searching "
                            "for local symmetries only", "False");

    Options options = parser.parse();
    if ((options.get_enum("symmetries_for_shrinking") == 0
            || options.get_enum("symmetries_for_shrinking") == 2)
         && (options.get_enum("internal_merging") == 1)) {
        parser.error("non-linear internal merging only affects when "
                     "using local symmetries for shrinking!");
    }

    if (parser.dry_run())
        return 0;
    else
        return new MergeSymmetries(options);
}

static Plugin<MergeStrategy> _plugin("merge_symmetries", _parse);
