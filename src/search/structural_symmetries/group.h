#ifndef STRUCTURAL_SYMMETRIES_GROUP_H
#define STRUCTURAL_SYMMETRIES_GROUP_H

#include <memory>
#include <vector>

class GlobalState;
class GraphCreator;
class Permutation;
class StateRegistry;

namespace options {
class Options;
}

enum class SearchSymmetries {
    NONE,
    OSS,
    DKS
};

class Group {
    // Options for the type of symmetries used
    bool stabilize_initial_state;
    SearchSymmetries search_symmetries;

    bool initialized;
    GraphCreator *graph_creator;
    std::vector<const Permutation *> generators;
    bool dump;

    // Methods for OSS
    typedef std::vector<short int> Trace;
    void get_trace(const GlobalState& state, Trace& full_trace) const;
    Permutation *compose_permutation(const Trace &) const;

    void delete_generators();

    // Moved from permutation
    int num_vars;
    int permutation_length;

public:
    const Permutation &get_permutation(int index) const;

    explicit Group(const options::Options &opts);
    ~Group();
    int num_identity_generators;
    void compute_symmetries();

    static void add_permutation(void*, unsigned int, const unsigned int *);
    void add_generator(const Permutation *gen);
    int get_num_generators() const;
    void dump_generators() const;
    void dump_variables_equivalence_classes() const;
    void statistics() const;
    bool is_stabilizing_initial_state() const {
        return stabilize_initial_state;
    }
    bool is_initialized() const {
        return initialized;
    }
    bool has_symmetries() const {
        return !generators.empty();
    }
    SearchSymmetries get_search_symmetries() const {
        return search_symmetries;
    }

    // Used for OSS
    int *get_canonical_representative(const GlobalState &state) const;
    // Used for path tracing (OSS and DKS)
    Permutation *create_permutation_from_state_to_state(
        const GlobalState &from_state, const GlobalState &to_state) const;


    // Moved from permutation
    std::vector<int> dom_sum_by_var;
    std::vector<int> var_by_val;
    void set_permutation_num_variables(int nvars) { num_vars = nvars; }
    int get_permutation_num_variables() const { return num_vars; }
    void set_permutation_length(int length) { permutation_length = length; }
    int get_permutation_length() const { return permutation_length; }

    int get_var_by_index(int val) const;
    std::pair<int, int> get_var_val_by_index(const int ind) const;
    int get_index_by_var_val_pair(const int var, const int val) const;

    Permutation* new_identity_permutation() const;
};

#endif