/**
 * TrustSnapshot.jsx — v13
 * Fixes:
 *  - Trust Score column: restored soft tinted gradient background keyed to verdict colour
 *  - Article Summary: font bumped to 15px, scroll window 260px
 *  - All other v12 improvements preserved
 */

import { useEffect, useState, useMemo, useRef } from "react";
import { createPortal } from "react-dom";
import { Progress } from "@/components/ui/progress";
import ReactMarkdown from "react-markdown";
import { HashLoader } from "react-spinners";
import { ClipboardList, ShieldCheck, Globe, Info } from "lucide-react";

// ─── Maths ────────────────────────────────────────────────────────────────────
function computeTrustScore({ factcheckResult, propagandaResult }) {
  const fR = Array.isArray(factcheckResult) && factcheckResult.length > 0;
  const pR = propagandaResult?.propaganda_probability !== undefined &&
             propagandaResult?.propaganda_probability !== null;
  if (!fR && !pR) return { ready: false, loadingServices: ["fact-check", "propaganda"] };
  if (!fR)        return { ready: false, loadingServices: ["fact-check"] };
  if (!pR)        return { ready: false, loadingServices: ["propaganda"] };

  const total = factcheckResult.length;
  const ws = factcheckResult.reduce((acc, f) => {
    const c = (f.correctness ?? "").toLowerCase();
    return acc + (c === "factual" ? 1 : c === "cannot be determined" ? 0.5 : 0);
  }, 0);
  const factScore = total > 0 ? (ws / total) * 50 : 0;
  const propScore = (1 - (propagandaResult.propaganda_probability ?? 0)) * 50;
  return { ready: true, score: Math.min(100, Math.max(0, factScore + propScore)), factScore, propScore };
}

const VERDICT = {
  Trustworthy:             { label: "Trustworthy",            emoji: "✅", color: "#064e3b", ring: "#6ee7b7", bar: "#10b981", track: "#a7f3d0", bgFrom: "#d1fae5", bgTo: "#ecfdf5", explanation: "This article appears factually sound with low influence language." },
  "Read with Caution":     { label: "Read with Caution",      emoji: "⚠️", color: "#78350f", ring: "#fcd34d", bar: "#f59e0b", track: "#fde68a", bgFrom: "#fef3c7", bgTo: "#fffbeb", explanation: "Some claims may need independent verification." },
  "Treat with Scepticism": { label: "Treat with Scepticism",  emoji: "🔶", color: "#7c2d12", ring: "#fdba74", bar: "#f97316", track: "#fed7aa", bgFrom: "#ffedd5", bgTo: "#fff7ed", explanation: "Notable signs of factual issues or influence techniques detected." },
  "Likely Misleading":     { label: "Likely Misleading",      emoji: "🚨", color: "#7f1d1d", ring: "#fca5a5", bar: "#ef4444", track: "#fecaca", bgFrom: "#fee2e2", bgTo: "#fef2f2", explanation: "Strong indicators of misinformation or propaganda." },
};
const getVerdict = s => s >= 70 ? VERDICT["Trustworthy"] : s >= 50 ? VERDICT["Read with Caution"] : s >= 30 ? VERDICT["Treat with Scepticism"] : VERDICT["Likely Misleading"];

const CRED_STYLE = {
  "Highly Credible":     { color: "#065f46", bg: "#d1fae5", border: "#6ee7b7", pillEmoji: "🏅" },
  "Moderately Credible": { color: "#1e40af", bg: "#dbeafe", border: "#93c5fd", pillEmoji: "👍" },
  Questionable:          { color: "#92400e", bg: "#fef3c7", border: "#fcd34d", pillEmoji: "🤔" },
  "Low Credibility":     { color: "#991b1b", bg: "#fee2e2", border: "#fca5a5", pillEmoji: "⛔" },
  "Insufficient Data":   { color: "#4b5563", bg: "#f3f4f6", border: "#d1d5db", pillEmoji: "❓" },
};

function domainFromUrl(url) { try { return new URL(url).hostname.replace("www.", ""); } catch { return url ?? ""; } }

// ─── Donut ────────────────────────────────────────────────────────────────────
function Donut({ score, color, track, size = 180 }) {
  const [anim, setAnim] = useState(0);
  const r = size / 2 - 15, circ = 2 * Math.PI * r;
  useEffect(() => {
    const s = Date.now(), d = 1100;
    const tick = () => {
      const p = Math.min((Date.now() - s) / d, 1);
      setAnim(score * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [score]);
  const cx = size / 2, cy = size / 2, dash = (Math.min(100, Math.max(0, anim)) / 100) * circ;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)", display: "block" }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={track} strokeWidth={15} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={15}
        strokeDasharray={`${dash} ${circ - dash}`} strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 6px ${color}99)` }} />
    </svg>
  );
}

// ─── Tooltip ─────────────────────────────────────────────────────────────────
function CalcTooltip({ trust, verdict }) {
  const ref = useRef(null);
  const [pos, setPos] = useState(null);
  const show = () => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const viewportCenter = r.left + r.width / 2 + window.scrollX;
    const tooltipHalf = 200;
    const margin = 14;
    const minX = window.scrollX + margin + tooltipHalf;
    const maxX = window.scrollX + window.innerWidth - margin - tooltipHalf;
    const x = Math.max(minX, Math.min(viewportCenter, maxX));
    setPos({ x, y: r.bottom + window.scrollY + 10 });
  };
  const hide = () => setPos(null);
  if (!trust?.ready) return null;
  const factPct = Math.round(trust.factScore), propPct = Math.round(trust.propScore);
  return (
    <>
      <button ref={ref} onMouseEnter={show} onMouseLeave={hide}
        style={{ display: "inline-flex", alignItems: "center", gap: 5, color: "#6b7280", background: "none", border: "none", padding: 0, cursor: "help" }}>
        <Info style={{ width: 15, height: 15 }} />
        <span className="text-sm" style={{ fontWeight: 600, textDecoration: "underline", textUnderlineOffset: 2 }}>How is this calculated?</span>
      </button>
      {pos && createPortal(
        <div style={{ position: "absolute", top: pos.y, left: pos.x, transform: "translateX(-50%)", zIndex: 9999, width: "min(400px, calc(100vw - 24px))", pointerEvents: "none" }}>
          <div style={{ width: 0, height: 0, borderLeft: "7px solid transparent", borderRight: "7px solid transparent", borderBottom: "7px solid #0f172a", margin: "0 auto" }} />
          <div className="text-sm" style={{ background: "#0f172a", borderRadius: 14, padding: "20px 22px", boxShadow: "0 16px 48px rgba(0,0,0,0.5)", lineHeight: 1.65 }}>
            <p className="text-base" style={{ fontWeight: 700, color: "#ffffff", marginBottom: 14 }}>How Trust Score Is Calculated</p>

            <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 16 }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span className="text-sm" style={{ color: "#e2e8f0" }}>✅ Fact Accuracy</span>
                  <span className="text-sm" style={{ fontWeight: 700, color: "#fff" }}>{factPct} / 50</span>
                </div>
                <div style={{ background: "#1e293b", borderRadius: 5, height: 9 }}>
                  <div style={{ background: "#10b981", borderRadius: 5, height: 9, width: `${(factPct / 50) * 100}%`, transition: "width 0.6s ease" }} />
                </div>
              </div>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span className="text-sm" style={{ color: "#e2e8f0" }}>🧠 Low Propaganda</span>
                  <span className="text-sm" style={{ fontWeight: 700, color: "#fff" }}>{propPct} / 50</span>
                </div>
                <div style={{ background: "#1e293b", borderRadius: 5, height: 9 }}>
                  <div style={{ background: "#6366f1", borderRadius: 5, height: 9, width: `${(propPct / 50) * 100}%`, transition: "width 0.6s ease" }} />
                </div>
              </div>
            </div>

            <div style={{ height: 1, background: "#1e293b", margin: "4px 0 12px" }} />

            <div className="text-sm" style={{ color: "#cbd5e1", lineHeight: 1.65 }}>
              <p style={{ margin: 0 }}>
                Trust Score uses <span style={{ color: "#ffffff", fontWeight: 600 }}>fact-checking</span> and <span style={{ color: "#ffffff", fontWeight: 600 }}>propaganda risk</span> because they are the most direct credibility signals.
              </p>
              <ul style={{ margin: "8px 0 8px", paddingLeft: 16 }}>
                <li>Fact-check points: factual = 1, cannot be determined = 0.5, unfactual = 0 (scaled to 50)</li>
                <li>Low propaganda contributes the other 50 points</li>
              </ul>
              <p style={{ margin: 0 }}>
                Sentiment and emotion are not included because tone is never fully unbiased. Political-bias ratings reflect perspective, not factual accuracy or credibility.
              </p>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

// ─── ColTitle ─────────────────────────────────────────────────────────────────
function ColTitle({ icon: Icon, iconColor = "#6366f1", children }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
      <div style={{ background: `${iconColor}1a`, borderRadius: 9, padding: "6px 7px", display: "flex", alignItems: "center" }}>
        <Icon style={{ color: iconColor, width: 22, height: 22 }} strokeWidth={1.75} />
      </div>
      <span className="text-xl" style={{ fontWeight: 700, color: "#111827", letterSpacing: -0.3 }}>{children}</span>
    </div>
  );
}

// ─── Smart summary renderer ───────────────────────────────────────────────────
// If the text already has markdown lists, render as-is.
// If it's plain prose paragraphs, split and render as bullet points.
function SummaryContent({ text, dotColor = "bg-violet-400" }) {
  const hasMarkdownList = /^[\s]*[-*\d]/m.test(text);

  if (hasMarkdownList) {
    return (
      <ReactMarkdown
        components={{
          ul: ({ children }) => <ul className="space-y-2.5">{children}</ul>,
          ol: ({ children }) => <ol className="space-y-2.5">{children}</ol>,
          li: ({ children }) => (
            <li className="flex items-start gap-2.5 leading-relaxed text-md">
              <span className={`shrink-0 rounded-full ${dotColor}`} style={{ marginTop: 8, width: 6, height: 6 }} />
              <span>{children}</span>
            </li>
          ),
          p: ({ children }) => <p className="leading-relaxed mb-2.5 text-md">{children}</p>,
          strong: ({ children }) => <span style={{ fontWeight: 600, color: "#111827" }}>{children}</span>,
        }}
      >
        {text}
      </ReactMarkdown>
    );
  }

  // Split into individual sentences, bullet each one
  const sentences = text
    .replace(/\n+/g, " ")          // flatten newlines
    .split(/(?<=[.!?])\s+/)        // split after punctuation
    .map(s => s.trim())
    .filter(s => s.length > 20);   // drop fragments

  return (
    <ul className="space-y-2">
      {sentences.map((s, i) => (
        <li key={i} className="flex items-start gap-2.5 text-md">
          <span className={`shrink-0 rounded-full ${dotColor}`} style={{ marginTop: 7, width: 6, height: 6 }} />
          <span style={{ color: "#374151", lineHeight: 1.6 }}>{s}</span>
        </li>
      ))}
    </ul>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
const TrustSnapshot = ({ data, apiUrl }) => {
  const [credibility, setCredibility] = useState(null);
  const [credLoading, setCredLoading] = useState(false);

  useEffect(() => {
    if (!apiUrl || !data?.url) return;
    const domain = domainFromUrl(data.url);
    setCredLoading(true);
    fetch(`${apiUrl}/application/source_credibility?domain=${encodeURIComponent(domain)}`)
      .then(r => r.json()).then(setCredibility)
      .catch(() => setCredibility(null)).finally(() => setCredLoading(false));
  }, [apiUrl, data?.url]);

  const trust = useMemo(
    () => data ? computeTrustScore({ factcheckResult: data.factcheck_result, propagandaResult: data.propaganda_result }) : null,
    [data]
  );
  if (!data) return null;

  const verdict   = trust?.ready ? getVerdict(trust.score) : null;
  const credStyle = credibility?.label ? CRED_STYLE[credibility.label] ?? CRED_STYLE["Insufficient Data"] : CRED_STYLE["Insufficient Data"];
  const isLowCred = credibility?.status === "ok" && (credibility.label === "Low Credibility" || credibility.label === "Questionable");

  // Restored: tinted gradient background for col 1
  const col1Bg = verdict
    ? `linear-gradient(160deg, ${verdict.bgFrom} 0%, ${verdict.bgTo} 100%)`
    : "linear-gradient(160deg, #f9fafb 0%, #f3f4f6 100%)";
  const col1Border = verdict ? `${verdict.ring}55` : "#e5e7eb";

  return (
    <div className="rounded-2xl overflow-hidden border border-gray-200" style={{ boxShadow: "0 2px 16px rgba(0,0,0,0.07)" }}>
      {verdict && <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, ${verdict.bar}, ${verdict.ring})` }} />}

      <div className="grid grid-cols-1 lg:grid-cols-3" style={{ minHeight: 280 }}>

        {/* ── COL 1 — Trust Score (tinted bg) ─────────────────────────── */}
        <div className="px-6 py-6 flex flex-col items-center gap-3 lg:border-r"
          style={{ background: col1Bg, borderColor: col1Border }}>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, width: "100%" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ background: verdict ? `${verdict.bar}22` : "#6366f118", borderRadius: 9, padding: "6px 7px", display: "flex", alignItems: "center" }}>
                <ShieldCheck style={{ color: verdict?.bar ?? "#6366f1", width: 22, height: 22 }} strokeWidth={1.75} />
              </div>
              <span className="text-xl" style={{ fontWeight: 700, color: "#111827", letterSpacing: -0.3 }}>Trust Score</span>
            </div>
            <CalcTooltip trust={trust} verdict={verdict} />
          </div>

          <div className="relative" style={{ width: 180, height: 180 }}>
            {trust?.ready ? (
              <>
                <Donut score={trust.score} color={verdict.bar} track={verdict.track} size={180} />
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span className="text-5xl" style={{ fontWeight: 900, color: verdict.color, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>
                    {trust.score.toFixed(0)}
                  </span>
                  <span className="text-sm" style={{ fontWeight: 700, color: "#9ca3af", marginTop: 2 }}>/ 100</span>
                </div>
              </>
            ) : (
              <div style={{ width: 180, height: 180, borderRadius: "50%", background: "rgba(255,255,255,0.5)" }} className="animate-pulse" />
            )}
          </div>

          {trust?.ready ? (
            <div className="w-full text-center space-y-1.5">
              <div className="text-sm" style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 8, width: "100%", padding: "9px 12px", borderRadius: 12, border: `2px solid ${verdict.ring}`, color: verdict.color, fontWeight: 800, background: "rgba(255,255,255,0.75)" }}>
                <span>{verdict.emoji}</span><span>{verdict.label}</span>
              </div>
              <p className="text-xs" style={{ color: verdict.color, opacity: 0.85, lineHeight: 1.55, padding: "0 4px" }}>{verdict.explanation}</p>
            </div>
          ) : (
            <p className="text-sm" style={{ color: "#6b7280", textAlign: "center" }}>
              {trust?.loadingServices?.length === 2 ? "Waiting for fact-check and propaganda…" : `Waiting for ${trust?.loadingServices?.[0]}…`}
            </p>
          )}
        </div>

        {/* ── COL 2 — Outlet Credibility ──────────────────────────────── */}
        <div className="px-6 py-6 flex flex-col gap-4 bg-white border-t lg:border-t-0 lg:border-r" style={{ borderColor: "#e5e7eb" }}>
          <ColTitle icon={Globe} iconColor="#0ea5e9">Outlet Credibility</ColTitle>
          {credLoading ? (
            <div className="space-y-3 animate-pulse">{[60, 80, 50].map((w, i) => <div key={i} className="h-4 bg-gray-100 rounded" style={{ width: `${w}%` }} />)}</div>
          ) : credibility?.status === "ok" ? (
            <>
              <div className="text-sm" style={{ display: "inline-flex", alignItems: "center", gap: 10, alignSelf: "flex-start", borderRadius: 999, padding: "9px 18px", border: `2px solid ${credStyle.border}`, background: credStyle.bg, color: credStyle.color, fontWeight: 700 }}>
                <span className="text-xl">{credStyle.pillEmoji}</span>
                <span>{credibility.label}</span>
              </div>
              {credibility.factual_accuracy_rate != null && (
                <div>
                  <div className="flex justify-between mb-1.5">
                    <span className="text-sm" style={{ fontWeight: 500, color: "#4b5563" }}>Average Accuracy</span>
                    <span className="text-sm" style={{ fontWeight: 700, color: "#111827" }}>{(credibility.factual_accuracy_rate * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={credibility.factual_accuracy_rate * 100} indicatorClassName="bg-teal-400" />
                </div>
              )}
              {credibility.avg_propaganda_probability != null && (
                <div>
                  <div className="flex justify-between mb-1.5">
                    <span className="text-sm" style={{ fontWeight: 500, color: "#4b5563" }}>Average Propaganda</span>
                    <span className="text-sm" style={{ fontWeight: 700, color: "#111827" }}>{(credibility.avg_propaganda_probability * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={credibility.avg_propaganda_probability * 100} indicatorClassName={credibility.avg_propaganda_probability > 0.5 ? "bg-rose-400" : "bg-amber-400"} />
                </div>
              )}
              {isLowCred && (
                <div className="flex items-start gap-2 p-3 rounded-lg border" style={{ background: credibility.label === "Low Credibility" ? "#fee2e2" : "#fef3c7", borderColor: credibility.label === "Low Credibility" ? "#fca5a5" : "#fcd34d" }}>
                  <span className="text-base shrink-0">{credibility.label === "Low Credibility" ? "🚩" : "⚠️"}</span>
                  <div>
                    <p className="text-sm" style={{ fontWeight: 700, color: credibility.label === "Low Credibility" ? "#991b1b" : "#92400e" }}>
                      {credibility.label === "Low Credibility" ? "Low credibility source" : "Questionable source"}
                    </p>
                    <p className="text-xs" style={{ marginTop: 3, lineHeight: 1.55, color: credibility.label === "Low Credibility" ? "#7f1d1d" : "#78350f" }}>
                      {credibility.label === "Low Credibility" ? "Past articles showed consistently low fact accuracy." : "This outlet has a below-average credibility record."}
                    </p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm" style={{ color: "#9ca3af", fontStyle: "italic" }}>
              {credibility?.status === "no_data" ? "No history for this source." : "Loading credibility data…"}
            </p>
          )}
        </div>

        <div className="px-6 py-6 flex flex-col bg-white border-t lg:border-t-0" style={{ borderColor: "#e5e7eb" }}>
          <ColTitle icon={ClipboardList} iconColor="#8b5cf6">Article Summary</ColTitle>
          <div className="mt-3 overflow-y-auto pr-1" style={{ maxHeight: 280 }}>
            {data?.summarise_result && typeof data.summarise_result === "string" && data.summarise_result.trim() ? (
              <SummaryContent text={data.summarise_result} dotColor="bg-violet-400" />
            ) : data?.summarise_result == null ? (
              <div className="flex items-center gap-3 py-3">
                <HashLoader color="#6366f1" size={16} />
                <p className="text-sm" style={{ color: "#9ca3af" }}>Generating summary…</p>
              </div>
            ) : null}
          </div>
        </div>

      </div>
    </div>
  );
};

export default TrustSnapshot;