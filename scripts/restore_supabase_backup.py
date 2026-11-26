"""Verify repository backup; optional recovery only into an existing empty row."""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backup import FIELDS,public_row,connect

ROOT=Path(__file__).resolve().parents[1]

def read_backup(root,backup_date):
    if date.fromisoformat(backup_date).isoformat()!=backup_date:raise ValueError("Invalid date")
    path=root/"backups"/("portfolio_backup_"+backup_date+".json")
    raw=path.read_bytes()
    checksum=path.with_suffix(".json.sha256")
    verified=checksum.is_file()
    if verified and hashlib.sha256(raw).hexdigest()!=checksum.read_text(encoding="ascii").strip():
        raise ValueError("Backup checksum mismatch")
    rows=json.loads(raw)
    if not isinstance(rows,list):raise ValueError("Invalid backup format")
    matches=[r for r in rows if isinstance(r,dict) and r.get("id")==1]
    if len(matches)!=1:raise ValueError("Expected exactly one portfolio row")
    return public_row(matches[0]),verified

def restore_empty(client,row,confirm):
    if confirm!="RESTORE_EMPTY":raise ValueError("Explicit confirmation required")
    # Query only the target row, then guard every core field against a
    # concurrent write. Never replace an active portfolio or approved policy.
    cols=(*FIELDS,"attribution_benchmark_policy")
    current=client.table("portfolio_db").select(",".join(cols)).eq("id",1).single().execute().data
    if not current or current["id"]!=1:raise ValueError("Existing empty target required")
    empty={"ledger_data":[],"history_data":[],"stock_meta":{},"settings":{},"attribution_benchmark_policy":None}
    if any(current[k] is not None and current[k]!=v for k,v in empty.items()):
        raise ValueError("Target is not empty")
    payload={k:v for k,v in row.items() if k!="id"}
    query=client.table("portfolio_db").update(payload).eq("id",1)
    for k in empty:
        v=current[k]
        query=query.is_(k,"null") if v is None else query.eq(k,json.dumps(v,separators=(",",":")))
    result=query.execute()
    if not isinstance(result.data,list) or len(result.data)!=1:raise ValueError("Conditional restore refused")
    after=client.table("portfolio_db").select(",".join(FIELDS)).eq("id",1).single().execute().data
    if after!=row:raise ValueError("Restore readback mismatch")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--backup-date",required=True)
    p.add_argument("--mode",choices=["verify","restore-empty"],default="verify")
    p.add_argument("--confirm",default="")
    a=p.parse_args()
    try:
        row,verified=read_backup(ROOT,a.backup_date)
        if a.mode=="verify":
            print("PUBLIC_BACKUP_VERIFIED" if verified else "LEGACY_BACKUP_FORMAT_OK_NO_CHECKSUM")
            return
        if not verified:raise ValueError("Legacy backup without checksum requires manual recovery")
        restore_empty(connect(),row,a.confirm)
        print("PUBLIC_RESTORE_OK")
    except Exception:
        print("PUBLIC_RECOVERY_BLOCKED: check backup, checksum, confirmation and empty target")
        raise SystemExit(1)

if __name__=="__main__":main()
