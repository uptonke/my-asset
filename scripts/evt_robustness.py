from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Sequence

import numpy as np
import pandas as pd
from scipy.stats import genpareto


def _empty_payload(
    *,
    alpha: float,
    primary_tail_fraction: float,
    threshold_grid: Sequence[float],
    n_boot: int,
    block_days: int,
    seed: int,
    status: str = "insufficient_sample",
) -> Dict[str, Any]:
    return {
        "status": status,
        "method": "pot_gpd_current_weight_daily_returns_with_block_bootstrap",
        "return_frequency": "daily",
        "horizon_days": 1,
        "alpha_conf": float(alpha),
        "sample_count": 0,
        "primary_tail_fraction": float(primary_tail_fraction),
        "primary_threshold_quantile": float(1.0 - primary_tail_fraction),
        "threshold_loss_pct": None,
        "exceedance_count": 0,
        "shape_xi": None,
        "scale_beta": None,
        "var95_pct": None,
        "es95_pct": None,
        "finite_upper_endpoint_loss_pct": None,
        "bootstrap_method": "circular_moving_block_bootstrap_recompute_threshold_refit_gpd",
        "bootstrap_replicates_requested": int(n_boot),
        "bootstrap_valid_reps": 0,
        "bootstrap_block_days": int(block_days),
        "bootstrap_seed": int(seed),
        "shape_xi_ci95_low": None,
        "shape_xi_ci95_high": None,
        "var95_ci95_low_pct": None,
        "var95_ci95_high_pct": None,
        "es95_ci95_low_pct": None,
        "es95_ci95_high_pct": None,
        "threshold_grid_tail_fractions": [float(x) for x in threshold_grid],
        "threshold_sensitivity": [],
        "threshold_valid_count": 0,
        "shape_xi_min": None,
        "shape_xi_max": None,
        "shape_xi_sign_stability": "insufficient",
        "evidence_flag": "insufficient_sample",
        "ci_interpretation": "sampling_uncertainty_conditional_on_current_weight_daily_return_proxy_not_predictive_interval",
        "limitations": [
            "Current-weight backcast: historical constituent weights are not reconstructed.",
            "Mixed-market daily closes can be asynchronous; closed-market prices may be forward-filled by the caller.",
            "POT/GPD results are threshold-sensitive and should not be treated as proof of the true tail class.",
        ],
    }


def _fit_gpd_at_tail_fraction(
    returns: np.ndarray,
    *,
    tail_fraction: float,
    alpha: float,
    min_exceedances: int,
) -> Dict[str, Any] | None:
    if not (0 < tail_fraction < 0.5) or not (0.5 < alpha < 1.0):
        return None
    if returns.size < max(30, min_exceedances * 2):
        return None

    losses = -returns
    threshold = float(np.quantile(losses, 1.0 - tail_fraction))
    exceed = losses[losses > threshold] - threshold
    n = int(losses.size)
    nu = int(exceed.size)
    if nu < int(min_exceedances):
        return None

    xi, _loc, beta = genpareto.fit(exceed, floc=0.0)
    xi = float(xi)
    beta = float(beta)
    if not (math.isfinite(xi) and math.isfinite(beta) and beta > 0):
        return None

    tail_prob = 1.0 - float(alpha)
    fu = nu / n
    if tail_prob <= 0 or fu <= tail_prob:
        return None

    if abs(xi) < 1e-8:
        var_loss = threshold + beta * math.log(fu / tail_prob)
    else:
        var_loss = threshold + (beta / xi) * (((fu / tail_prob) ** xi) - 1.0)

    es_loss = None
    if xi < 1.0:
        es_loss = (var_loss + beta - xi * threshold) / (1.0 - xi)

    endpoint = None
    if xi < 0:
        endpoint = threshold - beta / xi

    if not math.isfinite(var_loss):
        return None
    if es_loss is not None and not math.isfinite(es_loss):
        es_loss = None
    if endpoint is not None and not math.isfinite(endpoint):
        endpoint = None

    return {
        "tail_fraction": float(tail_fraction),
        "threshold_quantile": float(1.0 - tail_fraction),
        "threshold_loss_pct": float(threshold * 100.0),
        "exceedance_count": nu,
        "shape_xi": xi,
        "scale_beta": beta,
        "var_pct": float(-var_loss * 100.0),
        "es_pct": float(-es_loss * 100.0) if es_loss is not None else None,
        "finite_upper_endpoint_loss_pct": float(endpoint * 100.0) if endpoint is not None else None,
    }


def _percentile_ci(values: Iterable[float]) -> tuple[float | None, float | None, int]:
    arr = np.asarray([float(v) for v in values if v is not None and math.isfinite(float(v))], dtype=float)
    if arr.size < 100:
        return None, None, int(arr.size)
    lo, hi = np.quantile(arr, [0.025, 0.975])
    return float(lo), float(hi), int(arr.size)


def _evidence_flag(
    *,
    xi: float | None,
    xi_ci_low: float | None,
    xi_ci_high: float | None,
    sign_stability: str,
) -> str:
    if xi is None:
        return "insufficient_sample"
    if sign_stability == "all_positive" and xi_ci_low is not None and xi_ci_low > 0:
        return "positive_xi_robust_across_tested_thresholds"
    if sign_stability == "all_negative" and xi_ci_high is not None and xi_ci_high < 0:
        return "negative_xi_robust_across_tested_thresholds"
    if sign_stability == "mixed":
        return "threshold_sensitive_tail_shape"
    return "uncertain_tail_shape"


def compute_evt_robustness(
    port_returns: pd.Series | Iterable[float],
    *,
    alpha: float = 0.95,
    primary_tail_fraction: float = 0.10,
    threshold_grid: Sequence[float] = (0.075, 0.10, 0.125, 0.15),
    min_exceedances: int = 20,
    n_boot: int = 500,
    block_days: int = 5,
    seed: int = 42,
) -> Dict[str, Any]:
    """Robust POT/GPD diagnostic for a current-weight daily portfolio proxy."""
    base = _empty_payload(
        alpha=alpha,
        primary_tail_fraction=primary_tail_fraction,
        threshold_grid=threshold_grid,
        n_boot=n_boot,
        block_days=block_days,
        seed=seed,
    )

    try:
        s = pd.Series(port_returns, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
        values = s.to_numpy(dtype=float)
        n = int(values.size)
        base["sample_count"] = n
        if n < max(120, int(math.ceil(min_exceedances / max(primary_tail_fraction, 1e-6)))):
            return base

        primary = _fit_gpd_at_tail_fraction(
            values,
            tail_fraction=float(primary_tail_fraction),
            alpha=float(alpha),
            min_exceedances=int(min_exceedances),
        )
        if primary is None:
            return base

        sensitivity: list[dict[str, Any]] = []
        for tf in threshold_grid:
            fit = _fit_gpd_at_tail_fraction(
                values,
                tail_fraction=float(tf),
                alpha=float(alpha),
                min_exceedances=int(min_exceedances),
            )
            if fit is None:
                sensitivity.append({
                    "tail_fraction": float(tf),
                    "threshold_quantile": float(1.0 - tf),
                    "status": "insufficient_or_fit_failed",
                })
                continue
            sensitivity.append({
                "status": "available",
                **{k: (round(v, 6) if isinstance(v, float) else v) for k, v in fit.items()},
            })

        valid_sensitivity = [row for row in sensitivity if row.get("status") == "available"]
        xis = [float(row["shape_xi"]) for row in valid_sensitivity if row.get("shape_xi") is not None]
        if xis and all(x < 0 for x in xis):
            sign_stability = "all_negative"
        elif xis and all(x > 0 for x in xis):
            sign_stability = "all_positive"
        elif xis:
            sign_stability = "mixed"
        else:
            sign_stability = "insufficient"

        block_days = max(2, min(int(block_days), n))
        n_boot = max(0, int(n_boot))
        rng = np.random.default_rng(int(seed))
        blocks_needed = int(math.ceil(n / block_days))
        offsets = np.arange(block_days, dtype=int)

        xi_samples: list[float] = []
        var_samples: list[float] = []
        es_samples: list[float] = []

        for _ in range(n_boot):
            starts = rng.integers(0, n, size=blocks_needed)
            idx = ((starts[:, None] + offsets[None, :]) % n).reshape(-1)[:n]
            fit = _fit_gpd_at_tail_fraction(
                values[idx],
                tail_fraction=float(primary_tail_fraction),
                alpha=float(alpha),
                min_exceedances=int(min_exceedances),
            )
            if fit is None:
                continue
            xi_samples.append(float(fit["shape_xi"]))
            var_samples.append(float(fit["var_pct"]))
            if fit.get("es_pct") is not None:
                es_samples.append(float(fit["es_pct"]))

        xi_lo, xi_hi, xi_valid = _percentile_ci(xi_samples)
        var_lo, var_hi, var_valid = _percentile_ci(var_samples)
        es_lo, es_hi, es_valid = _percentile_ci(es_samples)
        valid_reps = min(xi_valid, var_valid, es_valid if primary.get("es_pct") is not None else var_valid)

        evidence = _evidence_flag(
            xi=float(primary["shape_xi"]),
            xi_ci_low=xi_lo,
            xi_ci_high=xi_hi,
            sign_stability=sign_stability,
        )

        base.update({
            "status": "available" if valid_reps >= 100 else "partial",
            "sample_count": n,
            "threshold_loss_pct": round(float(primary["threshold_loss_pct"]), 4),
            "exceedance_count": int(primary["exceedance_count"]),
            "shape_xi": round(float(primary["shape_xi"]), 6),
            "scale_beta": round(float(primary["scale_beta"]), 8),
            "var95_pct": round(float(primary["var_pct"]), 4),
            "es95_pct": round(float(primary["es_pct"]), 4) if primary.get("es_pct") is not None else None,
            "finite_upper_endpoint_loss_pct": round(float(primary["finite_upper_endpoint_loss_pct"]), 4) if primary.get("finite_upper_endpoint_loss_pct") is not None else None,
            "bootstrap_replicates_requested": n_boot,
            "bootstrap_valid_reps": int(valid_reps),
            "bootstrap_block_days": block_days,
            "shape_xi_ci95_low": round(xi_lo, 6) if xi_lo is not None else None,
            "shape_xi_ci95_high": round(xi_hi, 6) if xi_hi is not None else None,
            "var95_ci95_low_pct": round(var_lo, 4) if var_lo is not None else None,
            "var95_ci95_high_pct": round(var_hi, 4) if var_hi is not None else None,
            "es95_ci95_low_pct": round(es_lo, 4) if es_lo is not None else None,
            "es95_ci95_high_pct": round(es_hi, 4) if es_hi is not None else None,
            "threshold_sensitivity": sensitivity,
            "threshold_valid_count": int(len(valid_sensitivity)),
            "shape_xi_min": round(min(xis), 6) if xis else None,
            "shape_xi_max": round(max(xis), 6) if xis else None,
            "shape_xi_sign_stability": sign_stability,
            "evidence_flag": evidence,
        })
        return base
    except Exception as exc:
        base["status"] = "error"
        base["error"] = f"{type(exc).__name__}: {exc}"
        return base
