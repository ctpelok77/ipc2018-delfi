// HACK! Ignore this if used as a top-level compile target.
#ifdef OPEN_LISTS_TIEBREAKING_OPEN_LIST_H

#include "../evaluation_context.h"
#include "../option_parser.h"
#include "../scalar_evaluator.h"

#include <iostream>
#include <cassert>
#include <limits>

using namespace std;

/*
  Bucket-based implementation of a open list.
  Nodes with identical heuristic value are expanded in FIFO order.
*/

template<class Entry>
OpenList<Entry> *TieBreakingOpenList<Entry>::_parse(OptionParser &parser) {
    parser.document_synopsis("Tie-breaking open list", "");
    parser.add_list_option<ScalarEvaluator *>("evals", "scalar evaluators");
    parser.add_option<bool>(
        "pref_only",
        "insert only nodes generated by preferred operators", "false");
    parser.add_option<bool>(
        "unsafe_pruning",
        "allow unsafe pruning when the main evaluator regards a state a dead end",
        "true");
    Options opts = parser.parse();
    if (parser.dry_run())
        return 0;
    else
        return new TieBreakingOpenList<Entry>(opts);
}

template<class Entry>
TieBreakingOpenList<Entry>::TieBreakingOpenList(const Options &opts)
    : OpenList<Entry>(opts.get<bool>("pref_only")),
      size(0), evaluators(opts.get_list<ScalarEvaluator *>("evals")),
      allow_unsafe_pruning(opts.get<bool>("unsafe_pruning")) {
}

template<class Entry>
TieBreakingOpenList<Entry>::TieBreakingOpenList(
    const std::vector<ScalarEvaluator *> &evals,
    bool preferred_only, bool unsafe_pruning)
    : OpenList<Entry>(preferred_only), size(0), evaluators(evals),
      allow_unsafe_pruning(unsafe_pruning) {
}

template<class Entry>
TieBreakingOpenList<Entry>::~TieBreakingOpenList() {
}

template<class Entry>
void TieBreakingOpenList<Entry>::insert(
    EvaluationContext &eval_context, const Entry &entry) {
    if (OpenList<Entry>::only_preferred && !eval_context.is_preferred())
        return;
    if (eval_context.is_heuristic_infinite(evaluators[0])
        && allow_unsafe_pruning)
        return;

    vector<int> key;
    key.reserve(evaluators.size());
    for (ScalarEvaluator *evaluator : evaluators)
        key.push_back(eval_context.get_heuristic_value_or_infinity(evaluator));

    buckets[key].push_back(entry);
    ++size;
}

template<class Entry>
Entry TieBreakingOpenList<Entry>::remove_min(vector<int> *key) {
    assert(size > 0);
    typename std::map<const std::vector<int>, Bucket>::iterator it;
    it = buckets.begin();
    assert(it != buckets.end());
    assert(!it->second.empty());
    --size;
    if (key) {
        assert(key->empty());
        *key = it->first;
    }
    Entry result = it->second.front();
    it->second.pop_front();
    if (it->second.empty())
        buckets.erase(it);
    return result;
}

template<class Entry>
bool TieBreakingOpenList<Entry>::empty() const {
    return size == 0;
}

template<class Entry>
void TieBreakingOpenList<Entry>::clear() {
    buckets.clear();
    size = 0;
}

template<class Entry>
int TieBreakingOpenList<Entry>::dimension() const {
    return evaluators.size();
}

template<class Entry>
void TieBreakingOpenList<Entry>::get_involved_heuristics(std::set<Heuristic *> &hset) {
    for (size_t i = 0; i < evaluators.size(); ++i) {
        evaluators[i]->get_involved_heuristics(hset);
    }
}
#endif
