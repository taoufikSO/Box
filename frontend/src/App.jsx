import { useState } from "react";
const BACKEND = import.meta.env.VITE_BACKEND_URL;

export default function App() {
  const [tab, setTab] = useState("invoices"); // "invoices" | "stock"
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // options
  const [fmt, setFmt] = useState("csv");
  const [fuzzy, setFuzzy] = useState(90);
  const [dropDupes, setDropDupes] = useState(true);
  const [dropNeg, setDropNeg] = useState(false);
  const [flagDue, setFlagDue] = useState(true);
  const [daysExp, setDaysExp] = useState(30);

  const endpoint =
    tab === "invoices"
      ? `${BACKEND}/api/invoices/clean?fmt=${fmt}&fuzzy=${fuzzy}&drop_dupes=${dropDupes}&drop_negative_qty=${dropNeg}&flag_due_issue=${flagDue}`
      : `${BACKEND}/api/stock/clean?fmt=${fmt}&days_expiring=${daysExp}&drop_negative_qty=${dropNeg}`;

  const doClean = async () => {
    try {
      setBusy(true);
      setError(""); setResult(null);
      if (!file) throw new Error("Select a file first.");

      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(endpoint, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      setResult(json);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const openDownload = () => {
    if (!result?.download_token) return;
    window.open(`${BACKEND}/api/download/${result.download_token}`, "_blank");
  };

  const openShare = () => {
    if (!result?.download_token) return;
    window.open(`${BACKEND}${result.share_url}`, "_blank");
  };

  const sample = () => {
    const url = tab === "invoices" ? `${BACKEND}/api/sample/invoices` : `${BACKEND}/api/sample/stock`;
    window.open(url, "_blank");
  };

  return (
    <div style={{ maxWidth: 920, margin: "40px auto", color: "#ddd", fontFamily: "Inter, system-ui" }}>
      <h1 style={{ fontSize: 48 }}>AI in a Box — Demo</h1>
      <p>Upload a CSV/XLSX, tweak options, download/share the cleaned file.</p>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 12, margin: "20px 0" }}>
        <button onClick={() => setTab("invoices")} style={{ padding: "8px 14px", background: tab==="invoices" ? "#333":"#111" }}>Invoices</button>
        <button onClick={() => setTab("stock")} style={{ padding: "8px 14px", background: tab==="stock" ? "#333":"#111" }}>Stock</button>
        <button onClick={sample} style={{ marginLeft: "auto" }}>Use sample {tab}</button>
      </div>

      {/* Options */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 14 }}>
        <div>
          <label>Export format</label><br/>
          <select value={fmt} onChange={e=>setFmt(e.target.value)}>
            <option value="csv">CSV</option>
            <option value="xlsx">XLSX</option>
          </select>
        </div>
        {tab==="invoices" && (
          <>
            <div>
              <label>Fuzzy match</label><br/>
              <input type="number" value={fuzzy} onChange={e=>setFuzzy(Number(e.target.value))}/>
            </div>
            <div>
              <label><input type="checkbox" checked={dropDupes} onChange={e=>setDropDupes(e.target.checked)}/> Drop duplicates</label>
              <br/>
              <label><input type="checkbox" checked={flagDue} onChange={e=>setFlagDue(e.target.checked)}/> Flag due before issue</label>
            </div>
          </>
        )}
        {tab==="stock" && (
          <>
            <div>
              <label>Days expiring</label><br/>
              <input type="number" value={daysExp} onChange={e=>setDaysExp(Number(e.target.value))}/>
            </div>
          </>
        )}
        <div>
          <label><input type="checkbox" checked={dropNeg} onChange={e=>setDropNeg(e.target.checked)}/> Drop negative qty</label>
        </div>
      </div>

      {/* Upload */}
      <div style={{ display: "flex", gap: 12, margin: "12px 0" }}>
        <input type="file" accept=".csv,.xlsx" onChange={e=>setFile(e.target.files?.[0] || null)} />
        <button disabled={!file || busy} onClick={doClean}>{busy ? "Working..." : "Clean"}</button>
        {result?.download_token && (
          <>
            <button onClick={openDownload}>Download</button>
            <button onClick={openShare}>Open share link</button>
          </>
        )}
      </div>

      {error && <p style={{ color:"crimson" }}>Error: {error}</p>}

      {result && (
        <>
          <h3>Summary</h3>
          <pre style={{ background:"#111", padding:12 }}>
{JSON.stringify(result.summary, null, 2)}
          </pre>
        </>
      )}
    </div>
  );
}
