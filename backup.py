"""Owner-selected PUBLIC plaintext backup. Only designated portfolio fields."""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FIELDS=("id","ledger_data","history_data","stock_meta","settings")
SETTINGS_FIELDS=("exchangeRate","fireTargets","priceMap","liquidityBufferRatio")
# Refuse rather than alter a snapshot or publish a known sensitive field.
SENSITIVE={"password","passwd","secret","apikey","accesstoken","refreshtoken","authorization",
           "servicerolekey","supabasesecretkey","privatekey","backupkey","portfoliobackupkey",
           "sheeturl","evidenceref","credential","credentials"}

def check_fields(x):
    if isinstance(x,dict):
        for k,v in x.items():
            if "".join(c for c in str(k).lower() if c.isalnum()) in SENSITIVE:
                raise ValueError("Sensitive field present in selected data")
            check_fields(v)
    elif isinstance(x,list):
        for v in x:check_fields(v)

def public_row(row):
    if not isinstance(row,dict) or type(row.get("id")) is not int or row["id"]<=0:
        raise ValueError("Invalid portfolio row")
    out={k:row[k] for k in FIELDS}
    for k in ("ledger_data","history_data"):
        if not isinstance(out[k],list) or not out[k] or not all(isinstance(v,dict) for v in out[k]):
            raise ValueError("Missing or empty source data")
    dates=[r.get("date") for r in out["history_data"]]
    if any(not isinstance(d,str) for d in dates) or len(dates)!=len(set(dates)):
        raise ValueError("Invalid or duplicate NAV dates")
    if not isinstance(out["stock_meta"],dict) or not isinstance(out["settings"],dict):
        raise ValueError("Invalid source metadata")
    out["settings"]={k:out["settings"][k] for k in SETTINGS_FIELDS if k in out["settings"]}
    check_fields(out)
    json.dumps(out,allow_nan=False)
    return out

def encode(row):
    return (json.dumps([public_row(row)],ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8")

def write_backup(row,root=Path("."),now=None):
    now=now or datetime.now(ZoneInfo("Asia/Taipei"))
    name="backups/portfolio_backup_"+now.astimezone(ZoneInfo("Asia/Taipei")).date().isoformat()+".json"
    path=root/name
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=encode(row)
    digest=hashlib.sha256(raw).hexdigest()
    path.write_bytes(raw)
    path.with_suffix(".json.sha256").write_text(digest+"\n",encoding="ascii")
    if path.read_bytes()!=raw:raise ValueError("Backup readback mismatch")
    return name

def connect():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"],os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_SECRET_KEY"])

def main():
    try:
        client=connect()
        row=client.table("portfolio_db").select(",".join(FIELDS)).eq("id",1).single().execute().data
        name=write_backup(row)
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as f:f.write("path="+name+"\n")
        print("PUBLIC_BACKUP_OK",name)
    except Exception:
        print("PUBLIC_BACKUP_BLOCKED: source validation or database error")
        raise SystemExit(1)

if __name__=="__main__":main()
