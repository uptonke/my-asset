"""Phase 2 diagnostic-only solvers evaluated on the canonical optimizer snapshot."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import linprog, minimize

# Strict intersection of existing UI and v2.3 policy; cash aggregate cap is
# an explicit sandbox assumption, not a change to formal governance.
POLICY = {
    "single_max": .20, "taiwan_max": .30, "crypto_max": .15,
    "cash_min": .08, "cash_max": .20, "gold_min": .03, "gold_max": .07,
    "theme_single_max": .10, "crypto_theme_max": .35,
}
THEME_TICKERS = {"GRID", "IFRA", "PICK", "SRVR", "VNM"}
TOL = 1e-7


def constraint_matrix(tickers, buckets, policy=POLICY):
    if set(tickers) != set(buckets):
        raise ValueError("Missing asset classification; cannot establish policy")
    names, rows, limits = [], [], []
    bounds = [(0., min(policy["single_max"], policy["theme_single_max"])
               if t in THEME_TICKERS else policy["single_max"]) for t in tickers]

    def add(name, mask, upper, sign=1):
        names.append(name)
        rows.append(np.array(mask, dtype=float) * sign)
        limits.append(float(upper) * sign)

    for group, cap in (("taiwan_equity", "taiwan_max"), ("crypto", "crypto_max"),
                       ("cash", "cash_max"), ("gold", "gold_max")):
        add(cap, [buckets[t] == group for t in tickers], policy[cap])
    for group, floor in (("cash", "cash_min"), ("gold", "gold_min")):
        add(floor, [buckets[t] == group for t in tickers], policy[floor], -1)
    add("crypto_theme_max", [buckets[t] == "crypto" or t in THEME_TICKERS for t in tickers],
        policy["crypto_theme_max"])
    return np.stack(rows), np.array(limits), bounds, names


def feasibility(w, A, b, bounds):
    w = np.asarray(w, dtype=float)
    if not np.isfinite(w).all():
        return False
    return (abs(float(w.sum()) - 1.) <= TOL
            and bool(np.all(A @ w <= b + TOL))
            and all(lo-TOL <= x <= hi+TOL for x, (lo, hi) in zip(w, bounds)))


def solve_constrained(returns, buckets, kind, policy=POLICY):
    tickers = list(returns.columns)
    X = returns.to_numpy(dtype=float)
    n = len(tickers)
    if n < 2 or len(X) < 60 or not np.isfinite(X).all():
        return None, {"status": "INSUFFICIENT_SAMPLE"}
    A, b, bounds, names = constraint_matrix(tickers, buckets, policy)
    eq = np.ones((1, n))
    feasible = linprog(np.zeros(n), A_ub=A, b_ub=b, A_eq=eq,
                       b_eq=[1.], bounds=bounds, method="highs")
    if not feasible.success:
        return None, {"status": "INFEASIBLE" if feasible.status == 2 else "FAILED",
                      "message": str(feasible.message), "constraints": names}

    if kind == "variance":
        cov = np.cov(X, rowvar=False, ddof=1) * 252.
        # Scaling improves convergence for portfolios with small covariance.
        scale = max(float(np.max(np.abs(cov))), 1e-12)
        cov = cov / scale
        result = minimize(lambda w: float(w @ cov @ w), feasible.x,
                          jac=lambda w: 2. * cov @ w, method="SLSQP", bounds=bounds,
                          constraints=[{"type": "eq", "fun": lambda w: w.sum()-1.,
                                        "jac": lambda w: np.ones(n)},
                                       {"type": "ineq", "fun": lambda w: b-A@w,
                                        "jac": lambda w: -A}],
                          options={"maxiter": 1000, "ftol": 1e-12})
        w = result.x
        objective = "annualized sample variance"
    elif kind == "cvar":
        # Rockafellar-Uryasev empirical 95% CVaR LP:
        # min eta + sum(u)/(0.05*T), u >= -Xw-eta, u >= 0.
        T = len(X)
        tail = sparse.hstack([-sparse.csr_matrix(X), -np.ones((T, 1)), -sparse.eye(T)], format="csr")
        limits = sparse.hstack([sparse.csr_matrix(A), sparse.csr_matrix((len(b), T+1))], format="csr")
        E = sparse.csr_matrix(np.r_[np.ones(n), np.zeros(T+1)].reshape(1,-1))
        result = linprog(np.r_[np.zeros(n), 1., np.full(T, 1./(.05*T))],
                         A_ub=sparse.vstack([limits, tail], format="csr"),
                         b_ub=np.r_[b, np.zeros(T)], A_eq=E, b_eq=[1.],
                         bounds=bounds+[(None,None)]+[(0.,None)]*T, method="highs")
        w = result.x[:n] if result.success else None
        objective = "empirical 95% CVaR linear program"
    else:
        raise ValueError("Unknown objective: "+kind)
    if not result.success or w is None or not feasibility(w, A, b, bounds):
        return None, {"status": "FAILED", "message": str(result.message),
                      "constraints": names, "constraint_validated": False}
    # Do not clip or normalize the solution after optimization.
    return pd.Series(w, index=tickers), {
        "status": "OK", "objective": objective, "constraint_validated": True,
        "constraints": names, "max_inequality_excess": max(0., float(np.max(A @ w - b))),
        "weight_sum_error": abs(float(w.sum())-1.), "solver": "SLSQP" if kind == "variance" else "HiGHS",
    }


def hrp_lite_weights(returns):
    # Reuse the existing risk engine's exact EWMA and recursive bisection.
    import update_stock_meta as q
    cov = q.ewma_covariance_matrix(returns, lam=q.SYNTHETIC_EWMA_LAMBDA)
    if cov is None:
        raise ValueError("EWMA covariance unavailable")
    corr = q.corr_from_covariance(cov)
    if corr is None:
        raise ValueError("Correlation unavailable")
    # Same greedy algorithm, deterministic alphabetical tie-breaking.
    cols = list(corr.columns)
    if len(cols) <= 2:
        order = cols
    else:
        avg = corr.abs().replace(1., np.nan).mean().fillna(0.)
        order = [min(cols, key=lambda t: (float(avg[t]), t))]
        remaining = set(cols) - set(order)
        while remaining:
            last = order[-1]
            nxt = min(remaining, key=lambda t: (1.-float(corr.loc[last,t]) if pd.notna(corr.loc[last,t]) else 9., t))
            order.append(nxt)
            remaining.remove(nxt)
    w = q.recursive_bisection_weights(cov, order).reindex(returns.columns)
    if not np.isfinite(w).all() or (w < -TOL).any() or abs(float(w.sum())-1.) > TOL:
        raise ValueError("Invalid HRP-lite weights")
    ewma_vol = math.sqrt(max(0., float(w.to_numpy() @ cov.to_numpy() @ w.to_numpy()))) * 100.
    return w, {"status": "OK", "objective": "unconstrained EWMA HRP-lite",
               "lambda": q.SYNTHETIC_EWMA_LAMBDA, "ordered_tickers": order,
               "ewma_vol_pct": round(ewma_vol, 3), "constraint_validated": False}


def build_phase2_portfolios(returns, current, meta):
    from run_skfolio_sandbox import portfolio_metrics, weight_table, turnover

    portfolios = {}
    buckets = meta.get("asset_buckets", {})
    for key, kind in (("constrained_min_variance","variance"), ("constrained_cvar95","cvar"), ("hrp_lite_common","hrp")):
        try:
            if kind == "hrp":
                w, info = hrp_lite_weights(returns)
            elif meta.get("skipped"):
                w, info = None, {"status": "INCOMPLETE_UNIVERSE", "message": "Held assets missing or stale"}
            else:
                w, info = solve_constrained(returns, buckets, kind)
            if w is None:
                portfolios[key] = {"status": info["status"], "method": info, "diagnostic_only": True}
                continue
            m = portfolio_metrics(returns, w, key)
            portfolios[key] = {
                "status": m["status"], "metrics": m, "method": info,
                "weights": weight_table(w, current, top_n=len(returns.columns)),
                "turnover_vs_current_pct": round(turnover(w, current)*100., 2),
                "diagnostic_only": True,
                "constraint_validated": bool(info.get("constraint_validated", False)),
            }
        except Exception as exc:
            portfolios[key] = {"status": "FAILED", "method": {"message": str(exc)[:300]}, "diagnostic_only": True}
    return {"version": "v2.0", "snapshot_id": meta["snapshot_id"],
            "policy_pct": {k: v*100 for k,v in POLICY.items()}, "portfolios": portfolios,
            "scope": "sandbox_only_no_trade_approval", "execution_permission": False,
            "notes": [
                "Policy uses the stricter intersection of existing UI and backend limits; gold 3–7% is enforced for this sandbox; aggregate cash cap 20% is an explicit sandbox assumption.",
                "Crypto plus listed thematic ETFs is a policy proxy, not measured high-volatility exposure.",
                "CVaR objective uses empirical LP; reported ES uses the existing common quantile-tail mean convention, which may differ at ties.",
                "Metrics use the same TWD return matrix and weight basis; HRP-lite EWMA volatility is separate from common sample volatility.",
                "No expected-return or cost assumptions; no formal order or approval output."
            ]}
