from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from app.config import settings
from app.cleaning.pipeline import clean_invoices
from app.cleaning.stock import clean_stock
from app.exporters import export_xlsx_styled
from app.share import render_share_page

import pandas as pd
import tempfile, os, io, uuid

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMP_DIR = tempfile.gettempdir()
TOKENS: dict[str, str] = {}
TOKENS_KIND: dict[str, str] = {}

@app.get("/health")
def health(): return {"ok": True}

def _save_and_token(result: dict, fmt: str, prefix: str, kind: str):
    token = str(uuid.uuid4())
    ext = "xlsx" if fmt == "xlsx" else "csv"
    out_path = os.path.join(TMP_DIR, f"{prefix}_{token}.{ext}")

    df: pd.DataFrame = result["clean_df"]
    if fmt == "xlsx":
        data = export_xlsx_styled(df)
        with open(out_path, "wb") as f: f.write(data)
    else:
        df.to_csv(out_path, index=False, encoding="utf-8")

    TOKENS[token] = out_path
    TOKENS_KIND[token] = kind
    result = dict(result)
    result.pop("clean_df", None)
    result["download_token"] = token
    result["share_url"] = f"/share/{token}"
    return result

@app.post("/api/invoices/clean")
async def api_invoices_clean(
    file: UploadFile = File(...),
    fmt: str = "csv",
    fuzzy: int = 90,
    drop_dupes: bool = True,
    drop_negative_qty: bool = False,
    flag_due_issue: bool = True,
):
    raw = await file.read()
    name = (file.filename or "").lower()
    if not (name.endswith(".csv") or name.endswith(".xlsx")):
        raise HTTPException(400, "Only CSV/XLSX allowed.")

    try:
        df = pd.read_csv(io.BytesIO(raw)) if name.endswith(".csv") else pd.read_excel(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(400, f"Cannot read file: {e}")

    result = clean_invoices(df, config={
        "fuzzy_threshold": fuzzy,
        "drop_duplicates": drop_dupes,
        "drop_negative_qty": drop_negative_qty,
        "flag_due_before_issue": flag_due_issue
    })
    return JSONResponse(_save_and_token(result, fmt, "aibox_inv", "invoices"))

@app.post("/api/stock/clean")
async def api_stock_clean(
    file: UploadFile = File(...),
    fmt: str = "csv",
    days_expiring: int = 30,
    drop_negative_qty: bool = False,
):
    raw = await file.read()
    name = (file.filename or "").lower()
    if not (name.endswith(".csv") or name.endswith(".xlsx")):
        raise HTTPException(400, "Only CSV/XLSX allowed.")

    try:
        df = pd.read_csv(io.BytesIO(raw)) if name.endswith(".csv") else pd.read_excel(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(400, f"Cannot read file: {e}")

    result = clean_stock(df, days_expiring=days_expiring, drop_negative_qty=drop_negative_qty)
    return JSONResponse(_save_and_token(result, fmt, "aibox_stock", "stock"))

@app.get("/api/download/{token}")
def api_download(token: str):
    path = TOKENS.get(token)
    if not path or not os.path.exists(path): raise HTTPException(404, "Token not found")
    mime = "text/csv" if path.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(open(path, "rb"), media_type=mime,
        headers={"Content-Disposition": 'attachment; filename="cleaned.xlsx"' if path.endswith(".xlsx") else 'attachment; filename="cleaned.csv"'})

@app.get("/share/{token}")
def share_page(token: str):
    path = TOKENS.get(token)
    if not path or not os.path.exists(path): raise HTTPException(404, "Token not found")
    kind = TOKENS_KIND.get(token, "invoices")

    # if XLSX saved, convert to CSV for preview
    if path.endswith(".xlsx"):
        tmp_csv = path + ".csv"
        pd.read_excel(path).to_csv(tmp_csv, index=False)
        path = tmp_csv

    html = render_share_page(path, kind=kind, limit=200)
    return Response(content=html, media_type="text/html; charset=utf-8")

# sample endpoints (tiny CSVs)
@app.get("/api/sample/invoices")
def sample_inv():
    import pandas as pd, io
    df = pd.DataFrame([
        {"Invoice": "INV-1", "Issue_Date": "2024-01-05", "Due_Date": "2024-01-04", "Customer":"Acme", "Item":"Pen", "Qty":2, "Price":3.5},
        {"Invoice": "INV-2", "Issue_Date": "2024-02-01", "Due_Date": "2024-02-20", "Customer":"Globex", "Item":"Paper", "Qty":-1, "Price":5.0},
        {"Invoice": "INV-2", "Issue_Date": "2024-02-01", "Due_Date": "2024-02-20", "Customer":"Globex", "Item":"Paper", "Qty":1, "Price":5.0},
    ])
    out = io.StringIO(); df.to_csv(out, index=False); out.seek(0)
    return StreamingResponse(iter([out.getvalue().encode("utf-8")]),
                             media_type="text/csv",
                             headers={"Content-Disposition":'attachment; filename="sample_invoices.csv"'})

@app.get("/api/sample/stock")
def sample_stock():
    import pandas as pd, io
    df = pd.DataFrame([
        {"Name":"Milk","Qty":4,"Reorder":10,"Expiry":"2025-10-01"},
        {"Name":"Cheese","Qty":-2,"Reorder":5,"Expiry":"2025-11-10"},
        {"Name":"Bread","Qty":3,"Reorder":2,"Expiry":"2025-10-02"}
    ])
    out = io.StringIO(); df.to_csv(out, index=False); out.seek(0)
    return StreamingResponse(iter([out.getvalue().encode("utf-8")]),
                             media_type="text/csv",
                             headers={"Content-Disposition":'attachment; filename="sample_stock.csv"'})
