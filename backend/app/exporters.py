import io
import pandas as pd

def export_xlsx_styled(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned")
        # you can add formatting here if you want
    return out.getvalue()
