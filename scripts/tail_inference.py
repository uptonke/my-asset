from __future__ import annotations

import math
from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd


def _base_payload(
    *,
    n_boot: int,
    block_weeks: int,
    seed: int,
    sample_count: int = 0,
    downside_sample_count: int = 0,
    status: str = "insufficient_sample",
) -> Dict[str, Any]:
    return {
        "status": status,
        "method": "circular_moving_block_bootstrap_percentile_ci",
        "ci_level": 0.95,
        "bootstrap_replicates_requested": int(n_boot),
        "block_length_weeks": int(block_weeks),
        "seed": int(seed),
        "sample_count": int(sample_count),
        "downside_sample_count": int(downside_sample_count),
        "threshold_policy": "recompute_benchmark_P20_P10_within_each_bootstrap_sample; downside_mask_benchmark_lt_0",
        "ci_interpretation": "sampling_uncertainty_of_conditional_statistics_not_predictive_interval",
        "conditional_corr_ci95_low": None,
        "conditional_corr_ci95_high": None,
        "conditional_corr_valid_reps": 0,
        "crisis_corr_ci95_low": None,
        "crisis_corr_ci95_high": None,
        "crisis_corr_valid_reps": 0,
        "downside_beta_ci95_low": None,
        "downside_beta_ci95_high": None,
        "downside_beta_valid_reps": 0,
    }


def _safe_corr(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 3 or len(y) < 3:
        return None
    if float(np.std(x, ddof=1)) <= 1e-12 or float(np.std(y, ddof=1)) <= 1e-12:
        return None
    value = float(np.corrcoef(x, y)[0, 1])
    return value if math.isfinite(value) else None


def _safe_beta(port: np.ndarray, bench: np.ndarray) -> float | None:
    if len(port) < 3 or len(bench) < 3:
        return None
    bench_var = float(np.var(bench, ddof=1))
    if not math.isfinite(bench_var) or bench_var <= 1e-12:
        return None
    cov = float(np.cov(port, bench, ddof=1)[0, 1])
    beta = cov / bench_var
    return beta if math.isfinite(beta) else None


def _percentile_ci(values: Iterable[float]) -> tuple[float | None, float | None, int]:
    arr = np.asarray([float(v) for v in values if v is not None and math.isfinite(float(v))], dtype=float)
    if len(arr) < 100:
        return None, None, int(len(arr))
    low, high = np.quantile(arr, [0.025, 0.975])
    return float(low), float(high), int(len(arr))


def compute_tail_bootstrap_ci(
    port_returns: pd.Series | Iterable[float],
    benchmark_returns: pd.Series | Iterable[float],
    *,
    n_boot: int = 2000,
    block_weeks: int = 4,
    seed: int = 42,
) -> Dict[str, Any]:
    """Moving-block bootstrap CIs for conditional tail statistics.

    The paired weekly return series is resampled with circular moving blocks so
    short-range time dependence is retained better than with an IID bootstrap.
    P20/P10 benchmark thresholds are recomputed inside every bootstrap sample.
    Returned percentile intervals measure estimation uncertainty; they are not
    predictive intervals for future returns.
    """
    try:
        frame = pd.concat(
            [
                pd.Series(port_returns, dtype="float64").rename("port"),
                pd.Series(benchmark_returns, dtype="float64").rename("bench"),
            ],
            axis=1,
        ).replace([np.inf, -np.inf], np.nan).dropna()

        n = int(len(frame))
        downside_n = int((frame["bench"] < 0).sum()) if n else 0
        base = _base_payload(
            n_boot=n_boot,
            block_weeks=block_weeks,
            seed=seed,
            sample_count=n,
            downside_sample_count=downside_n,
        )

        if n < 24 or int(n_boot) < 200:
            return base

        block_weeks = max(2, min(int(block_weeks), n))
        n_boot = max(200, int(n_boot))
        rng = np.random.default_rng(int(seed))

        port = frame["port"].to_numpy(dtype=float)
        bench = frame["bench"].to_numpy(dtype=float)
        blocks_needed = int(math.ceil(n / block_weeks))
        offsets = np.arange(block_weeks, dtype=int)

        conditional_corr_samples: list[float] = []
        crisis_corr_samples: list[float] = []
        downside_beta_samples: list[float] = []

        for _ in range(n_boot):
            starts = rng.integers(0, n, size=blocks_needed)
            idx = ((starts[:, None] + offsets[None, :]) % n).reshape(-1)[:n]
            bp = port[idx]
            bb = bench[idx]

            q20 = float(np.quantile(bb, 0.20))
            q10 = float(np.quantile(bb, 0.10))

            cond_mask = bb <= q20
            crisis_mask = bb <= q10
            down_mask = bb < 0

            cond_corr = _safe_corr(bp[cond_mask], bb[cond_mask])
            crisis_corr = _safe_corr(bp[crisis_mask], bb[crisis_mask])
            down_beta = _safe_beta(bp[down_mask], bb[down_mask])

            if cond_corr is not None:
                conditional_corr_samples.append(cond_corr)
            if crisis_corr is not None:
                crisis_corr_samples.append(crisis_corr)
            if down_beta is not None:
                downside_beta_samples.append(down_beta)

        cond_low, cond_high, cond_valid = _percentile_ci(conditional_corr_samples)
        crisis_low, crisis_high, crisis_valid = _percentile_ci(crisis_corr_samples)
        beta_low, beta_high, beta_valid = _percentile_ci(downside_beta_samples)

        base.update(
            {
                "status": "available" if min(cond_valid, crisis_valid, beta_valid) >= 100 else "partial",
                "block_length_weeks": block_weeks,
                "bootstrap_replicates_requested": n_boot,
                "conditional_corr_ci95_low": cond_low,
                "conditional_corr_ci95_high": cond_high,
                "conditional_corr_valid_reps": cond_valid,
                "crisis_corr_ci95_low": crisis_low,
                "crisis_corr_ci95_high": crisis_high,
                "crisis_corr_valid_reps": crisis_valid,
                "downside_beta_ci95_low": beta_low,
                "downside_beta_ci95_high": beta_high,
                "downside_beta_valid_reps": beta_valid,
            }
        )
        return base
    except Exception as exc:
        base = _base_payload(n_boot=n_boot, block_weeks=block_weeks, seed=seed, status="error")
        base["error"] = f"{type(exc).__name__}: {exc}"
        return base
