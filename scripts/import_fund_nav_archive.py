"""Normalize verified public NAV downloads; no personal account records."""
import argparse
from pathlib import Path
import pandas as pd
from performance_market_data import FUND_CODES, merge_fund_archive

def import_archive(inputs, output):
    frames=[pd.read_csv(p,dtype=str,encoding="utf-8-sig") for p in inputs]
    output=Path(output)
    if output.exists():frames.insert(0,pd.read_csv(output,dtype=str,encoding="utf-8-sig"))
    cols=["ticker","fund_id","currency","date","nav","source"]
    for f in frames:
        if set(f.columns)!=set(cols):raise ValueError("Expected exact public NAV columns")
    data=pd.concat(frames,ignore_index=True)[cols]
    if data.empty or not data.ticker.isin(FUND_CODES).all():raise ValueError("Unknown fund")
    data["nav"]=pd.to_numeric(data.nav,errors="raise")
    if data[cols].isna().any().any():raise ValueError("Missing archive field")
    for _,g in data.groupby(["ticker","date"]):
        if g.nav.nunique()!=1 or g.fund_id.nunique()!=1 or g.currency.nunique()!=1:
            raise ValueError("Conflicting archive observations")
    for t,g in data.groupby("ticker"):
        if not (g.fund_id==FUND_CODES[t][0]).all() or not (g.currency=="TWD").all() or g.source.str.strip().eq("").any():
            raise ValueError("Archive identity, currency or source mismatch")
    data=data.drop_duplicates(["ticker","date"]).sort_values(["ticker","date"])
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_suffix(".tmp")
    try:
        data.to_csv(tmp,index=False)
        for t in data.ticker.unique():merge_fund_archive(t,pd.Series(dtype=float),tmp)
        tmp.replace(output)
    finally:
        if tmp.exists():tmp.unlink()
    return len(data)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("inputs",nargs="+")
    p.add_argument("--output",default="data/attribution/fund_nav_history.csv")
    args=p.parse_args()
    print("Validated public NAV rows:",import_archive(args.inputs,args.output))
