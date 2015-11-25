#ifndef MERGE_AND_SHRINK_MERGE_SCCS_H
#define MERGE_AND_SHRINK_MERGE_SCCS_H

#include "merge_strategy.h"

#include <unordered_set>

class MergeDFP;
class Options;

class MergeSCCs : public MergeStrategy {
    const Options *options;
    enum OrderOfSCCs {
        TOPOLOGICAL,
        REVERSE_TOPOLOGICAL,
        DECREASING,
        INCREASING
    };
    OrderOfSCCs order_of_sccs;
    enum InternalMergeOrder {
        LINEAR1,
        DFP1
    };
    InternalMergeOrder internal_merge_order;
    enum MergedSCCsMergeOrder {
        LINEAR2,
        DFP2
    };
    MergedSCCsMergeOrder merged_sccs_merge_order;
    std::vector<int> linear_variable_order;
    MergeDFP *merge_dfp;

    std::vector<std::unordered_set<int>> non_singleton_cg_sccs;
    std::vector<int> current_scc_ts_indices;
    bool merged_all_sccs;
    std::vector<int> indices_of_merged_sccs;
    bool start_merging_sccs;

    std::pair<int, int> get_next_linear(
        const std::shared_ptr<FactoredTransitionSystem> fts,
        const std::vector<int> available_indices,
        int most_recent_index,
        bool two_indices) const;
protected:
    virtual void dump_strategy_specific_options() const override {}
public:
    MergeSCCs(const Options &options);
    virtual ~MergeSCCs();
    virtual void initialize(const std::shared_ptr<AbstractTask> task) override;

    virtual std::pair<int, int> get_next(
        std::shared_ptr<FactoredTransitionSystem> fts) override;
    virtual std::string name() const override;
};

#endif
