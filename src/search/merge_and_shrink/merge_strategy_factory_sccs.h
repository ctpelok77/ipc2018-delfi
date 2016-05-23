#ifndef MERGE_AND_SHRINK_MERGE_STRATEGY_FACTORY_SCCS_H
#define MERGE_AND_SHRINK_MERGE_STRATEGY_FACTORY_SCCS_H

#include "merge_strategy_factory.h"

namespace options {
class Options;
}

namespace merge_and_shrink {
class MergeDFP;
class MergeStrategyFactorySCCs : public MergeStrategyFactory {
    const options::Options *options;
protected:
    virtual void dump_strategy_specific_options() const override;
public:
    MergeStrategyFactorySCCs(const options::Options &options);
    virtual ~MergeStrategyFactorySCCs();
    virtual std::unique_ptr<MergeStrategy> compute_merge_strategy(
        const std::shared_ptr<AbstractTask> &task,
        FactoredTransitionSystem &fts) override;
    virtual std::string name() const override;
};
}

#endif
