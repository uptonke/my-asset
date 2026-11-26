"""Authenticated encrypted private backup and empty-target recovery.

No plaintext files, no Git commits, no workflow artifacts. Only selected
portfolio row fields; derived analytics are rebuilt. Never log row values.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
from datetime import datetime,timezone
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BUCKET="portfolio-private-backups"
MAGIC=b"MYASSET-BACKUP-V1\x00"
FIELDS=("id","ledger_data","history_data","stock_meta","settings","attribution_benchmark_policy")
OBJECT_RE=re.compile(r"portfolio/v1/\d{8}T\d{6}Z-[0-9a-f]{24}\.enc")

def key_from_env():
    key=base64.b64decode(os.environ["PORTFOLIO_BACKUP_KEY"],validate=True)
    if len(key)!=32:raise ValueError("Backup key must contain 32 bytes")
    return key

def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

def validate_row(row):
    if not isinstance(row,dict) or set(row)!=set(FIELDS):raise ValueError("Backup field schema mismatch")
    if type(row["id"]) is not int or row["id"]<=0:raise ValueError("Invalid backup row ID")
    for k in ("ledger_data","history_data"):
        if not isinstance(row[k],list) or not row[k] or not all(isinstance(x,dict) for x in row[k]):
            raise ValueError("Invalid or empty backup ledger/history")
    if not isinstance(row["stock_meta"],dict) or not isinstance(row["settings"],dict):raise ValueError("Invalid backup metadata")
    if row["attribution_benchmark_policy"] is not None and not isinstance(row["attribution_benchmark_policy"],dict):
        raise ValueError("Invalid benchmark policy")
    dates=[x.get("date") for x in row["history_data"]]
    if any(not isinstance(d,str) for d in dates) or len(set(dates))!=len(dates):raise ValueError("Invalid or duplicate NAV dates")
    canonical(row)
    return row

def encrypt_row(row,key):
    validate_row(row)
    payload={"schema":"myasset-private-v1","created_at":datetime.now(timezone.utc).isoformat(),
             "row":row,"sha256":hashlib.sha256(canonical(row)).hexdigest()}
    nonce=secrets.token_bytes(12)
    return MAGIC+nonce+AESGCM(key).encrypt(nonce,canonical(payload),MAGIC)

def decrypt_row(blob,key):
    if not isinstance(blob,bytes) or not blob.startswith(MAGIC) or len(blob)<len(MAGIC)+28:
        raise ValueError("Invalid backup envelope")
    i=len(MAGIC);payload=json.loads(AESGCM(key).decrypt(blob[i:i+12],blob[i+12:],MAGIC))
    if payload.get("schema")!="myasset-private-v1":raise ValueError("Backup schema unsupported")
    row=validate_row(payload["row"])
    if hashlib.sha256(canonical(row)).hexdigest()!=payload["sha256"]:raise ValueError("Backup checksum mismatch")
    return row

def connect():
    from supabase import create_client
    url=os.environ["SUPABASE_URL"]
    key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_SECRET_KEY"]
    return create_client(url,key)

def private_bucket(client):
    meta=client.storage.get_bucket(BUCKET)
    public=meta.get("public") if isinstance(meta,dict) else getattr(meta,"public",None)
    if public is not False:raise ValueError("Backup bucket must be explicitly private")
    return client.storage.from_(BUCKET)

def row_id():
    return int(os.getenv("PORTFOLIO_ROW_ID","1"))

def backup(client,key):
    data=client.table("portfolio_db").select(",".join(FIELDS)).eq("id",row_id()).single().execute().data
    row=validate_row(data)
    blob=encrypt_row(row,key)
    bucket=private_bucket(client)
    name="portfolio/v1/"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+secrets.token_hex(12)+".enc"
    bucket.upload(name,blob,{"content-type":"application/octet-stream","upsert":"false"})
    received=bucket.download(name)
    if received!=blob or canonical(decrypt_row(received,key))!=canonical(row):raise ValueError("Backup readback mismatch")
    print("PRIVATE_BACKUP_OK",name)

def recover(client,key,name,mode,confirm):
    if not OBJECT_RE.fullmatch(name):raise ValueError("Invalid backup object path")
    row=decrypt_row(private_bucket(client).download(name),key)
    return recover_row(client,row,mode,confirm)

def recover_row(client,row,mode,confirm):
    validate_row(row)
    if row["id"]!=row_id():raise ValueError("Backup row mismatch")
    if mode=="verify":
        print("PRIVATE_BACKUP_VERIFIED");return
    if mode!="restore-empty" or confirm!="RESTORE_EMPTY":raise ValueError("Explicit restore confirmation required")
    result=client.rpc("restore_empty_portfolio_v27",{"p_row_id":row_id(),"p_data":row}).execute()
    if result.data is not True:raise ValueError("Restore refused: target not empty or missing")
    data=client.table("portfolio_db").select(",".join(FIELDS)).eq("id",row_id()).single().execute().data
    if canonical(data)!=canonical(row):raise ValueError("Restore readback mismatch")
    print("PRIVATE_RESTORE_OK")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["backup","verify","restore-empty","verify-local","restore-local-empty"])
    p.add_argument("--object",default="")
    p.add_argument("--file",default="")
    p.add_argument("--confirm",default="")
    a=p.parse_args()
    try:
        key=key_from_env()
        if a.mode=="verify-local":
            decrypt_row(Path(a.file).read_bytes(),key)
            print("PRIVATE_BACKUP_VERIFIED");return
        client=connect()
        if a.mode=="backup":backup(client,key)
        elif a.mode=="restore-local-empty":recover_row(client,decrypt_row(Path(a.file).read_bytes(),key),"restore-empty",a.confirm)
        else:recover(client,key,a.object,a.mode,a.confirm)
    except Exception:
        # No provider response, decrypted content, key or traceback in public CI.
        print("PRIVATE_BACKUP_OR_RECOVERY_BLOCKED: check key, private bucket, schema and target")
        raise SystemExit(1)

if __name__=="__main__":main()
