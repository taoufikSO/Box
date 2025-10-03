import pandas as pd
from rapidfuzz import fuzz

CANON_COLUMNS = {
    "invoice_id": ["invoice", "invoiceid", "invoice_id", "id", "inv_id"],
    "issue_date": ["issue_date", "date", "invoice_date"],
    "due_date":   ["due", "due_date", "payment_due"],
    "customer":   ["customer", "client", "buyer", "name"],
    "item":       ["item", "product", "sku", "description"],
    "qty":        ["qty", "quantity", "amount"],
    "price":      ["price", "unit_price", "cost"],
}

def _match_columns(df: pd.DataFrame, threshold=90) -> dict:
    mapping = {}
    cols = list(df.columns)
    for canon, candidates in CANON_COLUMNS.items():
        best = None
        best_score = 0
        for c in cols:
            for cand in candidates:
                s = fuzz.ratio(c.lower(), cand.lower())
                if s > best_score:
                    best_score = s
                    best = c
        if best_score >= threshold:
            mapping[canon] = best
    return mapping

def clean_invoices(df: pd.DataFrame, config: dict) -> dict:
    fuzzy = int(config.get("fuzzy_threshold", 90))
    drop_dupes = bool(config.get("drop_duplicates", True))
    drop_neg = bool(config.get("drop_negative_qty", False))
    flag_due_before_issue = bool(config.get("flag_due_before_issue", True))

    df = df.copy()

    # column mapping
    mapping = _match_columns(df, threshold=fuzzy)

    # create normalized columns
    out = pd.DataFrame()
    out["invoice_id"] = df[mapping.get("invoice_id")] if "invoice_id" in mapping else ""
    out["issue_date"] = pd.to_datetime(df[mapping["issue_date"]], errors="coerce") if "issue_date" in mapping else pd.NaT
    out["due_date"]   = pd.to_datetime(df[mapping["due_date"]], errors="coerce")   if "due_date" in mapping else pd.NaT
    out["customer"]   = df[mapping.get("customer")] if "customer" in mapping else ""
    out["item"]       = df[mapping.get("item")] if "item" in mapping else ""
    out["qty"]        = pd.to_numeric(df[mapping.get("qty")], errors="coerce") if "qty" in mapping else 0
    out["price"]      = pd.to_numeric(df[mapping.get("price")], errors="coerce") if "price" in mapping else 0.0

    out["total_before_tax"] = out["qty"] * out["price"]

    notes = []
    if flag_due_before_issue:
        due_before = (out["due_date"].notna()) & (out["issue_date"].notna()) & (out["due_date"] < out["issue_date"])
        notes.append(("DUE_BEFORE_ISSUE", due_before))

    if drop_neg:
        neg = out["qty"] < 0
        notes.append(("NEGATIVE_QTY", neg))
        out = out[~neg]

    if drop_dupes and "invoice_id" in out.columns:
        out = out.drop_duplicates(subset=["invoice_id"], keep="first")

    # build issues column
    issues = []
    for i in range(len(out)):
        flags = [name for name, mask in notes if mask.iloc[i] if len(mask) == len(out)]
        issues.append("|".join(flags))
    out["__issues"] = issues

    # Summary counts
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
