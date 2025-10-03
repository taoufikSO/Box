import { useState } from "react";

// IMPORTANT: set this in Vercel → Project → Settings → Environment Variables
// VITE_BACKEND_URL = https://<your-railway>.up.railway.app
const BACKEND = import.meta.env.VITE_BACKEND_URL;

export default function App() {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [downloadToken, setDownloadToken] = useState("");
  const [shareUrl, setShareUrl] = useState("");

  const clean = async () => {
    try {
      setBusy(true);
      setError("");
      setDownloadToken("");
      setShareUrl("");

      if (!file) throw new Error("Please choose a CSV or XLSX file first.");

      const fd = new FormData();
      fd.append("file", file);

      // This matches your previous backend endpoint & defaults
      const url =
        `${BACKEND}/api/clean?` +
        new URLSearchParams({
          fmt: "csv",
          fuzzy: "90",
          drop_dupes: "true",
          drop_negative_qty: "false",
          flag_due_issue: "true",
        }).toString();

      const res = await fetch(url, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());

      const json = await res.json();
      setDownloadToken(json.download_token || "");
      setShareUrl(json.share_url ? `${BACKEND}${json.share_url}` : "");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.wrap}>
        <h1 style={styles.h1}>AI in a Box — Demo</h1>
        <p style={styles.sub}>Upload a CSV/XLSX — backend will “clean” and give a download link.</p>

        <div style={styles.row}>
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <button style={styles.btn} onClick={clean} disabled={busy || !file}>
            {busy ? "Cleaning…" : "Clean"}
          </button>
        </div>

        {error && <p style={styles.err}>Error: {error}</p>}

        {downloadToken && (
          <div style={{ marginTop: 20 }}>
            <a
              style={styles.linkBtn}
              href={`${BACKEND}/api/download/${downloadToken}`}
              target="_blank"
              rel="noreferrer"
            >
              Download
            </a>
            {shareUrl && (
              <a
                style={{ ...styles.linkBtn, marginLeft: 12 }}
                href={shareUrl}
                target="_blank"
                rel="noreferrer"
              >
                Open share link
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#222",
    color: "#eee",
    fontFamily: "system-ui, Segoe UI, Inter, sans-serif",
  },
  wrap: { maxWidth: 900, margin: "60px auto", padding: "0 20px" },
  h1: { fontSize: 56, margin: "0 0 18px" },
  sub: { opacity: 0.85, margin: "0 0 24px" },
  row: { display: "flex", gap: 12, alignItems: "center" },
  btn: {
    background: "#1f6feb",
    border: "none",
    color: "#fff",
    padding: "10px 18px",
    borderRadius: 6,
    cursor: "pointer",
  },
  linkBtn: {
    display: "inline-block",
    background: "#444",
    color: "#fff",
    padding: "8px 14px",
    borderRadius: 6,
    textDecoration: "none",
  },
  err: { color: "crimson", marginTop: 16 },
};
