import pandas as pd
from datetime import datetime, timedelta

def clean_stock(df: pd.DataFrame, days_expiring=30, drop_negative_qty=False) -> dict:
    df = df.copy()

    # try to find basic fields
    name_col = next((c for c in df.columns if c.lower() in ("name","item","product","title","sku","description")), df.columns[0])
    qty_col  = next((c for c in df.columns if c.lower() in ("qty","quantity","stock","onhand","on_hand")), None)
    exp_col  = next((c for c in df.columns if "exp" in c.lower()), None)
    reorder_col = next((c for c in df.columns if "reorder" in c.lower() or "min" in c.lower()), None)

    out = pd.DataFrame()
    out["name"] = df[name_col].astype(str)
    out["qty"]  = pd.to_numeric(df[qty_col], errors="coerce") if qty_col else 0
    out["reorder_point"] = pd.to_numeric(df[reorder_col], errors="coerce") if reorder_col else 0
    out["expiry_date"] = pd.to_datetime(df[exp_col], errors="coerce") if exp_col else pd.NaT

    today = datetime.utcnow().date()
    soon = today + timedelta(days=int(days_expiring))

    issues = []
    for _, r in out.iterrows():
        f = []
        if r["qty"] <= r["reorder_point"]:
            f.append("LOW_STOCK")
        if pd.notna(r["expiry_date"]):
            d = r["expiry_date"].date()
            if d <= today:
                f.append("EXPIRED")
            elif d <= soon:
                f.append("EXPIRING_SOON")
        if drop_negative_qty and r["qty"] < 0:
            f.append("NEGATIVE_QTY")
        issues.append("|".join(f))

    if drop_negative_qty:
        out = out[out["qty"] >= 0]

    out["__issues"] = issues

    counts = pd.Series(out["__issues"].fillna("").str.split("|").explode().value_counts()).to_dict()
    counts.pop("", None)

    return {
        "clean_df": out.reset_index(drop=True),
        "summary": {
            "rows_in": len(df),
            "rows_out": len(out),
            "issue_counts": counts
        }
    }
