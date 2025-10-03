from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io, os, uuid, tempfile

app = FastAPI(title="AI in a Box - Demo API", version="0.1.0")

# CORS: set via env CORS_ORIGINS or default to local dev
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMP_DIR = tempfile.gettempdir()
TOKENS: dict[str, str] = {}

@app.get("/")
def root():
    return {"ok": True, "name": "AI in a Box API", "version": "0.1.0"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/clean")
async def clean(file: UploadFile = File(...)):
    name = (file.filename or "").lower()
    if not (name.endswith(".csv") or name.endswith(".xlsx")):
        raise HTTPException(400, "Only CSV or XLSX files are allowed")

    raw = await file.read()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
        else:
            df = pd.read_excel(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {e}")

    # --- FAKE CLEANING: just add a new column ---
    df["__note"] = "cleaned_demo"

    # Save to temp CSV for download
    token = str(uuid.uuid4())
    out_path = os.path.join(TMP_DIR, f"aibox_{token}.csv")
    df.to_csv(out_path, index=False)

    return JSONResponse({
        "rows_in": len(df),
        "message": "Cleaned successfully (demo).",
        "download_token": token,
        "preview": df.head(5).fillna("").astype(str).to_dict(orient="records"),
    })

@app.get("/api/download/{token}")
def download(token: str):
    # Serve the temp CSV file
    for name in os.listdir(TMP_DIR):
        if name.startswith("aibox_") and token in name:
            full = os.path.join(TMP_DIR, name)
            return StreamingResponse(
                open(full, "rb"),
                media_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="cleaned.csv"'},
            )
    raise HTTPException(404, "Token not found")
