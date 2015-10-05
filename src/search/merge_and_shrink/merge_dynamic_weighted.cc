#include "merge_dynamic_weighted.h"

#include "transition_system.h"

#include "../causal_graph.h"
#include "../option_parser.h"
#include "../plugin.h"
#include "../task_proxy.h"


using namespace std;

// Helper methods to deal with transition systems

int compute_number_of_product_transitions(
    const TransitionSystem *ts1, const TransitionSystem *ts2) {
    // NOTE: this is copied from the merge constructor of TransitionSystem
    /*
      Note that this computes the number of tranistions in the product
      without considering possible shrinking due to unreachable or
      irrelevant states, which hence may reduce the actual number of
      transitions in the product.
    */
    int number_of_transitions = 0;
    for (TSConstIterator group1_it = ts1->begin();
         group1_it != ts1->end(); ++group1_it) {
        // Distribute the labels of this group among the "buckets"
        // corresponding to the groups of ts2.
        unordered_map<int, vector<int> > buckets;
        for (LabelConstIter label_it = group1_it.begin();
             label_it != group1_it.end(); ++label_it) {
            int label_no = *label_it;
            int group2_id = ts2->get_group_id_for_label(label_no);
            buckets[group2_id].push_back(label_no);
        }
        // Now buckets contains all equivalence classes that are
        // refinements of group1.

        // Now create the new groups together with their transitions.
        const vector<Transition> &transitions1 = group1_it.get_transitions();
        for (const auto &bucket : buckets) {
            const vector<Transition> &transitions2 =
                ts2->get_transitions_for_group_id(bucket.first);
            int new_transitions_for_new_group = transitions1.size() * transitions2.size();
            number_of_transitions += new_transitions_for_new_group;
        }
    }
    return number_of_transitions;
}

double compute_average_h_value(const TransitionSystem *ts) {
    int num_states = ts->get_size();
    int sum_distances = 0;
    for (int state = 0; state < num_states; ++state) {
        sum_distances += ts->get_goal_distance(state);
    }
    if (num_states == 0) {
        // For unsolvable transition systems
        return INF;
    }
    return static_cast<double>(sum_distances) / static_cast<double>(num_states);
}

// ========================= FEATURE CLASSES ===============================

Feature::Feature(int id, string name, bool merge_required, int weight)
    : id(id),
      name(name),
      merge_required(merge_required),
      weight(weight) {
}

double Feature::compute_unnormalized_value(const TransitionSystem *ts1,
                                           const TransitionSystem *ts2,
                                           const TransitionSystem *merge) {
    if (weight) {
        // TODO: get rid of this? we currently also perform this check
        // outside of this method before calling it
        return compute_value(ts1, ts2, merge);
    }
    return 0;
}

void Feature::dump() const {
    cout << name << ": " << weight << endl;
}

CausalConnectionFeature::CausalConnectionFeature(int id, int weight)
    : Feature(id, "causally connected variables", false, weight),
      causal_graph(0) {
}

CausalConnectionFeature::~CausalConnectionFeature() {
    delete causal_graph;
}

double CausalConnectionFeature::compute_value(const TransitionSystem *ts1,
                                              const TransitionSystem *ts2,
                                              const TransitionSystem *) {
    const vector<int> ts1_var_nos = ts1->get_incorporated_variables();
    vector<int> ts1_cg_neighbors;
    for (int var_no : ts1_var_nos) {
        const vector<int> &ts1_cg_successors = causal_graph->get_successors(var_no);
        ts1_cg_neighbors.insert(ts1_cg_neighbors.end(), ts1_cg_successors.begin(),
                                ts1_cg_successors.end());
        const vector<int> &ts1_cg_predecessors = causal_graph->get_predecessors(var_no);
        ts1_cg_neighbors.insert(ts1_cg_neighbors.end(), ts1_cg_predecessors.begin(),
                                ts1_cg_predecessors.end());
    }
    // NOTE: we want to count directed edges, to take into account if there
    // is a connection between variables in both directions or not.
//    sort(ts1_cg_neighbors.begin(), ts1_cg_neighbors.end());
//    ts1_cg_neighbors.erase(unique(ts1_cg_neighbors.begin(), ts1_cg_neighbors.end()),
//                           ts1_cg_neighbors.end());

    const vector<int> ts2_var_nos = ts2->get_incorporated_variables();
    int edge_count = 0;
    for (int ts1_cg_neighbor : ts1_cg_neighbors) {
        for (int ts2_var_no : ts2_var_nos) {
            if (ts2_var_no == ts1_cg_neighbor) {
                ++edge_count;
            }
        }
    }
    double max_possible_edges = ts1_var_nos.size() * ts2_var_nos.size() * 2;
    return static_cast<double>(edge_count) / max_possible_edges;
}

void CausalConnectionFeature::initialize(const TaskProxy &task_proxy, bool dump) {
    // TODO: avoid recreating a new causal graph (cannot assign a const
    // reference in this method)
    causal_graph = new CausalGraph(task_proxy);
    if (dump) {
        cout << "causal graph:" << endl;
        for (VariableProxy var : task_proxy.get_variables()) {
            cout << "successors for var " << var.get_id() << ": "
                 << causal_graph->get_successors(var.get_id()) << endl;
        }
    }
}

NonAdditivityFeature::NonAdditivityFeature(int id, int weight)
    : Feature(id, "non additive variables", false, weight) {
}

double NonAdditivityFeature::compute_value(const TransitionSystem *ts1,
                                           const TransitionSystem *ts2,
                                           const TransitionSystem *) {
    const vector<int> ts1_var_nos = ts1->get_incorporated_variables();
    const vector<int> ts2_var_nos = ts2->get_incorporated_variables();
    int not_additive_pair_count = 0;
    for (int ts1_var_no : ts1_var_nos) {
        for (int ts2_var_no : ts2_var_nos) {
            if (!additive_var_pairs[ts1_var_no][ts2_var_no]) {
                ++not_additive_pair_count;
            }
        }
    }
    // NOTE: in contrast to the causally connected variables feature,
    // we consider every pair only once.
    double total_pair_count = ts1_var_nos.size() * ts2_var_nos.size();
    return static_cast<double>(not_additive_pair_count) / total_pair_count;
}

void NonAdditivityFeature::initialize(const TaskProxy &task_proxy, bool dump) {
    int num_variables = task_proxy.get_variables().size();
    additive_var_pairs.resize(num_variables, vector<bool>(num_variables, true));
    for (OperatorProxy op : task_proxy.get_operators()) {
        for (EffectProxy e1 : op.get_effects()) {
            for (EffectProxy e2 : op.get_effects()) {
                int e1_var_id = e1.get_fact().get_variable().get_id();
                int e2_var_id = e2.get_fact().get_variable().get_id();
                additive_var_pairs[e1_var_id][e2_var_id] = false;
            }
        }
    }
    if (dump) {
        for (int var_no1 = 0; var_no1 < num_variables; ++var_no1) {
            for (int var_no2 = var_no1 + 1; var_no2 < num_variables; ++var_no2) {
                cout << var_no1 << " and " << var_no2 << ": "
                     << (additive_var_pairs[var_no1][var_no2] ? "" : "not ")
                     << "additive" << endl;
            }
        }
    }
}

TransStatesQuotFeature::TransStatesQuotFeature(int id, int weight)
    : Feature(id, "transitions per states quotient", false, weight) {
}

double TransStatesQuotFeature::compute_value(const TransitionSystem *ts1,
                                             const TransitionSystem *ts2,
                                             const TransitionSystem *) {
    double product_states = ts1->get_size() * ts2->get_size();
    double product_transitions = compute_number_of_product_transitions(ts1, ts2);
    return product_states / product_transitions;
}

InitHImprovementFeature::InitHImprovementFeature(int id, int weight)
    : Feature(id, "initial h value improvement", true, weight) {
}

double InitHImprovementFeature::compute_value(const TransitionSystem *ts1,
                                              const TransitionSystem *ts2,
                                              const TransitionSystem *merge) {
    assert(merge);
    int new_init_h;
    if (merge->is_solvable()) {
        new_init_h = merge->get_init_state_goal_distance();
    } else {
        // initial state has been pruned
        new_init_h = INF;
    }
    int old_init_h = max(ts1->get_init_state_goal_distance(),
                         ts2->get_init_state_goal_distance());
    int difference = new_init_h - old_init_h;
    if (!difference) {
        return 0;
    }
    if (!old_init_h) {
        return 1;
    }
    return static_cast<double>(difference) / static_cast<double>(old_init_h);
}

AvgHImprovementFeature::AvgHImprovementFeature(int id, int weight)
    : Feature(id, "average h value improvement", true, weight) {
}

double AvgHImprovementFeature::compute_value(const TransitionSystem *ts1,
                                             const TransitionSystem *ts2,
                                             const TransitionSystem *merge) {
    assert(merge);
    double new_average_h = compute_average_h_value(merge);
    double old_average_h = max(compute_average_h_value(ts1),
                               compute_average_h_value(ts2));
    double difference = new_average_h - old_average_h;
    if (!difference) {
        return 0;
    }
    if (!old_average_h) {
        return 1;
    }
    return static_cast<double>(difference) / static_cast<double>(old_average_h);
}

InitHSumFeature::InitHSumFeature(int id, int weight)
    : Feature(id, "initial h value sum", false, weight) {
}

double InitHSumFeature::compute_value(const TransitionSystem *ts1,
                                      const TransitionSystem *ts2,
                                      const TransitionSystem *) {
    int init_h_sum = ts1->get_init_state_goal_distance() +
        ts2->get_init_state_goal_distance();
    return init_h_sum;
}

AvgHSumFeature::AvgHSumFeature(int id, int weight)
    : Feature(id, "average h value sum", false, weight) {
}

double AvgHSumFeature::compute_value(const TransitionSystem *ts1,
                                     const TransitionSystem *ts2,
                                     const TransitionSystem *) {
    double average_h_sum = compute_average_h_value(ts1) +
        compute_average_h_value(ts2);
    return average_h_sum;
}

// ========================= FEATURES ====================================

Features::Features(const Options opts)
    : debug(opts.get<bool>("debug")) {
    int id = 0;
    features.push_back(new CausalConnectionFeature(
                           id++, opts.get<int>("w_causally_connected_vars")));
    features.push_back(new NonAdditivityFeature(
                           id++, opts.get<int>("w_nonadditive_vars")));
    features.push_back(new TransStatesQuotFeature(
                           id++, opts.get<int>("w_small_transitions_states_quotient")));
    features.push_back(new InitHImprovementFeature(
                           id++, opts.get<int>("w_high_initial_h_value_improvement")));
    features.push_back(new AvgHImprovementFeature(
                           id++, opts.get<int>("w_high_average_h_value_improvement")));
    features.push_back(new InitHSumFeature(
                           id++, opts.get<int>("w_high_initial_h_value_sum")));
    features.push_back(new AvgHSumFeature(
                           id++, opts.get<int>("w_high_average_h_value_sum")));
}

void Features::initialize(const shared_ptr<AbstractTask> task) {
    task_proxy = new TaskProxy(*task);
    for (Feature *feature : features) {
        if (feature->get_weight()) {
            feature->initialize(*task_proxy, debug);
        }
    }
    clear();
}

Features::~Features() {
    delete task_proxy;
    for (Feature *feature : features) {
        delete feature;
    }
}

void Features::update_min_max(int feature_id, double value) {
    if (value > max_values[feature_id]) {
        max_values[feature_id] = value;
    }
    if (value < min_values[feature_id]) {
        min_values[feature_id] = value;
    }
}

double Features::normalize_value(int feature_id, double value) const {
    double min = min_values[feature_id];
    double max = max_values[feature_id];
    if (max - min == 0) {
        // all three values are the same
        assert(min == value);
        assert(max == value);
        return 0;
    }
    double result = (value - min) / (max - min);
    assert(result >= 0);
    assert(result <= 1);
    return result;
}

void Features::precompute_unnormalized_values(TransitionSystem *ts1,
                                              TransitionSystem *ts2) {
    TransitionSystem *merge = 0;
    vector<double> values;
    values.reserve(features.size());
    for (Feature *feature : features) {
        if (feature->get_weight()) {
            if (feature->requires_merge() && !merge) {
                merge = new TransitionSystem(*task_proxy,
                                             ts1->get_labels(),
                                             ts1, ts2, false);
            }
            double value = feature->compute_unnormalized_value(ts1, ts2, merge);
            update_min_max(feature->get_id(), value);
            values.push_back(value);
        } else {
            // dummy value for correct indices
            values.push_back(-1);
        }
    }
    unnormalized_values[make_pair(ts1, ts2)] = values;
    delete merge;
}

double Features::compute_weighted_normalized_sum(
    TransitionSystem *ts1, TransitionSystem *ts2) const {
    const std::vector<double> &values = unnormalized_values.at(make_pair(ts1, ts2));
    double weighted_sum = 0;
    if (debug) {
        cout << "computing weighted normalized sum for "
             << ts1->tag() << ts2->tag() << endl;
    }
    for (Feature *feature : features) {
        if (feature->get_weight()) {
            double normalized_value = normalize_value(feature->get_id(),
                                                      values[feature->get_id()]);
            if (debug) {
                cout << "normalized value for feature " << feature->get_name()
                     << ": " << normalized_value << endl;
            }
            weighted_sum += feature->get_weight() * normalized_value;
        }
    }
    if (debug) {
        cout << "weighted normalized sum: " << weighted_sum << endl;
    }
    return weighted_sum;
}

void Features::clear() {
    min_values.assign(features.size(), INF);
    max_values.assign(features.size(), -1);
    unnormalized_values.clear();
}

void Features::dump_weights() const {
    for (Feature *feature : features) {
        feature->dump();
    }
}

// ========================= MERGE STRATEGY ===============================

MergeDynamicWeighted::MergeDynamicWeighted(const Options opts)
    : MergeStrategy() {
    features = new Features(opts);
}

MergeDynamicWeighted::~MergeDynamicWeighted() {
    delete features;
}

void MergeDynamicWeighted::dump_strategy_specific_options() const {
    features->dump_weights();
}

void MergeDynamicWeighted::initialize(const shared_ptr<AbstractTask> task) {
    MergeStrategy::initialize(task);
    TaskProxy task_proxy(*task);
    int num_variables = task_proxy.get_variables().size();
    var_no_to_ts_index.reserve(num_variables);
    for (VariableProxy var : task_proxy.get_variables()) {
        var_no_to_ts_index.push_back(var.get_id());
    }
    merge_order.reserve(num_variables * 2 - 1);
    features->initialize(task);
}

pair<int, int> MergeDynamicWeighted::get_next(const vector<TransitionSystem *> &all_transition_systems) {
    int ts_index1 = -1;
    int ts_index2 = -1;

    if (remaining_merges == 1) {
        // Return the first pair
        ts_index1 = 0;
        while (!all_transition_systems[ts_index1]) {
            ++ts_index1;
        }
        assert(in_bounds(ts_index1, all_transition_systems));
        ts_index2 = ts_index1 + 1;
        while (!all_transition_systems[ts_index2]) {
            ++ts_index2;
        }
        assert(in_bounds(ts_index2, all_transition_systems));
    } else {
        // Go through all transitition systems and compute unnormalized feature values.
        for (size_t i = 0; i < all_transition_systems.size(); ++i) {
            TransitionSystem *ts1 = all_transition_systems[i];
            if (ts1) {
                for (size_t j = i + 1; j < all_transition_systems.size(); ++j) {
                    TransitionSystem *ts2 = all_transition_systems[j];
                    if (ts2) {
                        features->precompute_unnormalized_values(ts1, ts2);
                    }
                }
            }
        }

        // Go through all transition systems again and normalize feature values.
        int max_weight = -1;
        for (size_t i = 0; i < all_transition_systems.size(); ++i) {
            TransitionSystem *ts1 = all_transition_systems[i];
            if (ts1) {
                for (size_t j = i + 1; j < all_transition_systems.size(); ++j) {
                    TransitionSystem *ts2 = all_transition_systems[j];
                    if (ts2) {
                        int pair_weight =
                            features->compute_weighted_normalized_sum(
                                all_transition_systems[i], all_transition_systems[j]);
                        if (pair_weight > max_weight) {
                            max_weight = pair_weight;
                            ts_index1 = i;
                            ts_index2 = j;
                        }
                    }
                }
            }
        }
        assert(max_weight != -1);
        /*
          TODO: cache results for all transition systems? only two of the
          transition systems disappear each merge, and only one new arises.
          However, we would need to remove all pairs that the merge transition
          systems were part of, and compute all the pairs with the new one.

          Also, we would need to make sure that at the time that the
          merge strategy is asked for the next pair, the cached results are
          correct, i.e. the transition systems cannot have been shrunk in
          the meantime.
        */
        features->clear();
    }

    assert(ts_index1 != -1);
    assert(ts_index2 != -1);
    int new_ts_index = all_transition_systems.size();
    TransitionSystem *ts1 = all_transition_systems[ts_index1];
    TransitionSystem *ts2 = all_transition_systems[ts_index2];
    for (int var_no : ts1->get_incorporated_variables()) {
        var_no_to_ts_index[var_no] = new_ts_index;
    }
    for (int var_no : ts2->get_incorporated_variables()) {
        var_no_to_ts_index[var_no] = new_ts_index;
    }
    --remaining_merges;
    merge_order.push_back(make_pair(ts_index1, ts_index2));
    if (!remaining_merges) {
        cout << "merge order: ";
        for (auto merge : merge_order) {
            cout << "(" << merge.first << ", " << merge.second << "), ";
        }
        cout << endl;
    }
    return make_pair(ts_index1, ts_index2);
}

std::string MergeDynamicWeighted::name() const {
    return "dynamic merging";
}

static shared_ptr<MergeStrategy>_parse(OptionParser &parser) {
    parser.add_option<bool>(
        "debug", "debug", "false");
    parser.add_option<int>(
        "w_causally_connected_vars",
        "prefer merging variables that are causally connected ",
        "0",
        Bounds("0", "100"));
    parser.add_option<int>(
        "w_nonadditive_vars",
        "avoid merging additive variables",
        "0",
        Bounds("0", "100"));
    parser.add_option<int>(
        "w_small_transitions_states_quotient",
        "prefer merging 'sparse' transition systems",
        "0",
        Bounds("0", "100"));
    parser.add_option<int>(
        "w_high_initial_h_value_improvement",
        "prefer merging transition systems with high initial h value",
        "0",
        Bounds("0", "100"));
    parser.add_option<int>(
        "w_high_average_h_value_improvement",
        "prefer merging transition systems with high average h value",
        "0",
        Bounds("0", "100"));
    parser.add_option<int>(
        "w_high_initial_h_value_sum",
        "prefer merging transition systems with large number of states",
        "0",
        Bounds("0", "100"));
    parser.add_option<int>(
        "w_high_average_h_value_sum",
        "prefer merging transition systems with large number of edges",
        "0",
        Bounds("0", "100"));

    Options opts = parser.parse();
    if (opts.get<int>("w_causally_connected_vars") == 0 &&
        opts.get<int>("w_nonadditive_vars") == 0 &&
        opts.get<int>("w_small_transitions_states_quotient") == 0 &&
        opts.get<int>("w_high_initial_h_value_improvement") == 0 &&
        opts.get<int>("w_high_average_h_value_improvement") == 0 &&
        opts.get<int>("w_high_initial_h_value_sum") == 0 &&
        opts.get<int>("w_high_average_h_value_sum") == 0) {
        cerr << "you must specify at least one non-zero weight!" << endl;
        exit_with(EXIT_INPUT_ERROR);
    }

    if (parser.dry_run())
        return nullptr;
    else
        return make_shared<MergeDynamicWeighted>(opts);
}

static PluginShared<MergeStrategy> _plugin("merge_dynamic_weighted", _parse);
