import { useState } from "react";

const BACKEND = import.meta.env.VITE_BACKEND_URL;

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const onUpload = async () => {
    if (!file) return;
    setBusy(true);
    setError("");
    setResult(null);

    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${BACKEND}/api/clean`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      setResult(json);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", fontFamily: "Inter, system-ui" }}>
      <h1>AI in a Box – Demo</h1>
      <p>Upload a CSV/XLSX – backend will “clean” (demo) and give a download link.</p>

      <input
        type="file"
        accept=".csv,.xlsx"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button disabled={!file || busy} onClick={onUpload} style={{ marginLeft: 12 }}>
        {busy ? "Processing…" : "Clean"}
      </button>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 24 }}>
          <h3>Result</h3>
          <pre style={{ background: "#111", color: "#0f0", padding: 12 }}>
            {JSON.stringify(result, null, 2)}
          </pre>

          {result.download_token && (
            <a
              href={`${BACKEND}/api/download/${result.download_token}`}
              target="_blank"
              rel="noreferrer"
            >
              Download cleaned CSV
            </a>
          )}
        </div>
      )}
    </div>
  );
}
