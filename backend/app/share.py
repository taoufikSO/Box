import pandas as pd
import html

def render_share_page(csv_path: str, kind="invoices", limit=200) -> str:
    df = pd.read_csv(csv_path)
    head = df.head(limit)

    # very simple HTML preview
    table = head.to_html(index=False, escape=True)
    title = f"AI-in-a-Box preview – {html.escape(kind)}"
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; background:#0b0b0b; color:#ddd; padding:20px; }}
    table {{ border-collapse: collapse; font-size:14px; }}
    th, td {{ border:1px solid #333; padding:6px 10px; }}
    a {{ color:#7bd; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>First {len(head)} rows.</p>
  {table}
</body>
</html>"""
