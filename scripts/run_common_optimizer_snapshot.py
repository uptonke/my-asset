#!/usr/bin/env python3
"""Run all three solvers/diagnostics using one shared in-memory snapshot."""
import copy
import os

import run_skfolio_sandbox as skfolio
import run_riskfolio_sandbox as riskfolio
import run_optimizer_robustness as robustness


def main():
    returns, weights, meta = skfolio.load_strict_returns_and_weights()

    def shared_loader():
        return returns.copy(deep=True), weights.copy(deep=True), copy.deepcopy(meta)

    print("Shared optimizer snapshot:", meta["snapshot_id"], meta["strict_end"])
    if os.getenv("RUNNER_TEMP"):
        from run_cost_aware_optimizer import save_snapshot, snapshot_path
        save_snapshot(snapshot_path(), returns, weights, meta)
    for module in (skfolio, riskfolio, robustness):
        module.load_strict_returns_and_weights = shared_loader
        module.main()


if __name__ == "__main__":
    main()
