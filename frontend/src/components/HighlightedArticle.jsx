/**
 * HighlightedArticle.jsx — v7
 * Imports all matching logic from @/utils/highlightUtils (single source of truth).
 * Legend pills show technique definitions on hover.
 */

import { useMemo, useState, useCallback, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { findPhraseInContent } from "@/utils/propagandaHighlight";
import {
  getHighlightStyle, getLegendItems,
  splitToParagraphs, buildHlMap, hlMapToSegs,
} from "@/utils/highlightUtils";
import { X, ExternalLink } from "lucide-react";

const SENTIMENT_BG     = { positive: "#dcfce7", negative: "#fee2e2", neutral: "#fef9c3" };
const SENTIMENT_BORDER = { positive: "#4ade80", negative: "#f87171", neutral: "#fbbf24" };
const SENTIMENT_COLOR  = { positive: "#166534", negative: "#991b1b", neutral: "#854d0e" };
const SENTIMENT_LABEL  = { positive: "Positive 😊", negative: "Negative 😟", neutral: "Neutral 😐" };
const SENTIMENT_DEF    = { positive: "Expresses support, optimism, or agreement.", negative: "Expresses criticism, concern, or conflict.", neutral: "Reports facts without strong emotional language." };

const FACTCHECK_STYLE = {
  factual:                { bg: "#ccfbf1", border: "#5eead4", label: "Factual ✅",   color: "#0f766e" },
  "cannot be determined": { bg: "#fef3c7", border: "#fcd34d", label: "Unclear 🔍",   color: "#92400e" },
  unfactual:              { bg: "#ffe4e6", border: "#fda4af", label: "Unfactual ❌", color: "#9f1239" },
};
const FACTCHECK_TOOLTIPS = {
  factual:                "Verified as factually accurate. Click for details.",
  "cannot be determined": "Could not be independently verified. Click for details.",
  unfactual:              "Found to be inaccurate. Click for details.",
};
const FACTCHECK_DEF = {
  factual:                "Verified as factually accurate.",
  "cannot be determined": "Could not be independently verified.",
  unfactual:              "Found to be inaccurate.",
};

const MODES = [
  { id: "factcheck",  label: "✅ Fact-Check" },
  { id: "sentiment",  label: "😐 Sentiment"  },
  { id: "propaganda", label: "🔴 Propaganda" },
];

function computePopupPos(anchorRect, popupW, popupH, margin = 8) {
  const vw = window.innerWidth, vh = window.innerHeight, scrollY = window.scrollY, scrollX = window.scrollX;
  const fitsBelow = vh - anchorRect.bottom >= popupH + margin, fitsAbove = anchorRect.top >= popupH + margin;
  let top, arrowSide;
  if (fitsBelow) { top = anchorRect.bottom + scrollY + margin; arrowSide = "top"; }
  else if (fitsAbove) { top = anchorRect.top + scrollY - popupH - margin; arrowSide = "bottom"; }
  else { top = scrollY + margin; arrowSide = "none"; }
  let left = anchorRect.left + scrollX + anchorRect.width / 2 - popupW / 2;
  left = Math.max(scrollX + margin, Math.min(left, scrollX + vw - popupW - margin));
  return { top, left, arrowSide };
}

function WhiteTooltip({ label, def, accentColor, anchorRect, visible }) {
  const ref = useRef(null); const [pos, setPos] = useState({ top: 0, left: 0, arrowSide: "top" });
  useEffect(() => { if (!visible || !anchorRect || !ref.current) return; setPos(computePopupPos(anchorRect, ref.current.offsetWidth || 240, ref.current.offsetHeight || 72)); }, [visible, anchorRect]);
  if (!visible) return null;
  const ab = { position: "absolute", width: 0, height: 0, left: "50%", transform: "translateX(-50%)" };
  return createPortal(
    <div ref={ref} style={{ position: "absolute", top: pos.top, left: pos.left, zIndex: 9999, width: 240, pointerEvents: "none" }}>
      {pos.arrowSide === "bottom" && <div style={{ ...ab, bottom: -6, borderTop: "6px solid #e5e7eb", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }} />}
      {pos.arrowSide === "top"    && <div style={{ ...ab, top: -6, borderBottom: "6px solid #e5e7eb", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }} />}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderLeft: `3px solid ${accentColor}`, borderRadius: 8, padding: "8px 12px", boxShadow: "0 4px 16px rgba(0,0,0,0.10)", fontSize: 13, lineHeight: 1.5 }}>
        <p style={{ fontWeight: 700, color: accentColor, marginBottom: 3 }}>{label}</p>
        <p style={{ color: "#6b7280", margin: 0 }}>{def}</p>
      </div>
    </div>, document.body
  );
}

const FACT_POPUP_STYLE = {
  factual:                { bg: "#f0fdf4", border: "#86efac", color: "#166534", label: "Factual ✅" },
  "cannot be determined": { bg: "#fffbeb", border: "#fcd34d", color: "#92400e", label: "Unclear 🔍" },
  unfactual:              { bg: "#fff1f2", border: "#fda4af", color: "#9f1239", label: "Unfactual ❌" },
};
const showCites = f => { if (!f?.citations?.length) return false; const e = (f.explanation || "").toLowerCase(); return !["no sources","no source","sources do not","do not mention","does not mention"].some(p => e.includes(p)); };

function FactPopup({ fact, anchorRect, onClose }) {
  const ref = useRef(null); const [pos, setPos] = useState({});
  useEffect(() => { if (!anchorRect || !ref.current) return; const w = Math.min(ref.current.offsetWidth || 360, window.innerWidth - 16); const h = ref.current.offsetHeight || 200; setPos({ ...computePopupPos(anchorRect, w, h), width: w }); }, [anchorRect]);
  useEffect(() => { const h = e => { if (ref.current && !ref.current.contains(e.target)) onClose(); }; const t = setTimeout(() => document.addEventListener("mousedown", h), 50); return () => { clearTimeout(t); document.removeEventListener("mousedown", h); }; }, [onClose]);
  const c = (fact?.correctness ?? "cannot be determined").toLowerCase();
  const style = FACT_POPUP_STYLE[c] ?? FACT_POPUP_STYLE["cannot be determined"];
  const ab = { position: "absolute", width: 0, height: 0, left: "50%", transform: "translateX(-50%)" };
  return createPortal(
    <div ref={ref} style={{ position: "absolute", top: pos.top, left: pos.left, zIndex: 10000, width: pos.width || 360, maxWidth: "calc(100vw - 16px)" }}>
      {pos.arrowSide === "bottom" && <div style={{ ...ab, bottom: -6, borderTop: "6px solid #e5e7eb", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }} />}
      {pos.arrowSide === "top"    && <div style={{ ...ab, top: -6, borderBottom: "6px solid #e5e7eb", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }} />}
      <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderTop: `3px solid ${style.border}`, borderRadius: 10, boxShadow: "0 8px 32px rgba(0,0,0,0.18)", overflow: "hidden" }}>
        <div className="flex items-center justify-between px-4 py-3" style={{ background: style.bg, borderBottom: `1px solid ${style.border}` }}>
          <span className="text-sm font-bold uppercase tracking-wide" style={{ color: style.color }}>{style.label}</span>
          <button onMouseDown={e => { e.stopPropagation(); onClose(); }} className="p-1.5 rounded-lg hover:bg-black/10 flex-shrink-0" style={{ color: style.color, cursor: "pointer" }}><X className="h-4 w-4" /></button>
        </div>
        <div className="px-4 py-3 border-b border-gray-100"><p className="text-xs font-bold uppercase text-gray-400 mb-1">Claim</p><p className="text-sm text-gray-800 leading-relaxed font-medium">{fact?.statement}</p></div>
        <div className="px-4 py-3 border-b border-gray-100"><p className="text-xs font-bold uppercase text-gray-400 mb-1">Explanation</p><p className="text-sm text-gray-600 leading-relaxed italic">{fact?.explanation}</p></div>
        <div className="px-4 py-3"><p className="text-xs font-bold uppercase text-gray-400 mb-1.5">Sources</p>
          {showCites(fact) ? <ul className="space-y-1.5">{fact.citations.map((cit, ci) => <li key={ci} className="flex items-start gap-1.5 text-sm"><span className="font-semibold text-blue-500 shrink-0">[{ci + 1}]</span><a href={cit} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline break-all flex items-center gap-1">{cit.length > 55 ? cit.slice(0, 55) + "…" : cit}<ExternalLink className="h-3 w-3 shrink-0" /></a></li>)}</ul>
          : <p className="text-sm text-gray-400 italic">No verifying sources found</p>}
        </div>
      </div>
    </div>, document.body
  );
}

function HighlightSpan({ part }) {
  const ref = useRef(null), timer = useRef(null);
  const [hover, setHover] = useState(false), [rect, setRect] = useState(null), [open, setOpen] = useState(false);
  const onEnter = useCallback(() => { clearTimeout(timer.current); if (ref.current) setRect(ref.current.getBoundingClientRect()); setHover(true); }, []);
  const onLeave = useCallback(() => { timer.current = setTimeout(() => setHover(false), 120); }, []);
  useEffect(() => () => clearTimeout(timer.current), []);
  const onClick = useCallback(e => { if (part.mode === "factcheck") { e.stopPropagation(); if (ref.current) setRect(ref.current.getBoundingClientRect()); setOpen(v => !v); setHover(false); } }, [part.mode]);
  let bg, borderColor, accentColor, label, def;
  if (part.mode === "propaganda") { const s = getHighlightStyle(part.highlight); bg = s.bg; accentColor = s.color ?? "#374151"; label = s.label; def = s.def; borderColor = "transparent"; }
  else if (part.mode === "sentiment") { const hl = part.highlight ?? "neutral"; bg = SENTIMENT_BG[hl] ?? SENTIMENT_BG.neutral; borderColor = SENTIMENT_BORDER[hl] ?? SENTIMENT_BORDER.neutral; accentColor = SENTIMENT_COLOR[hl] ?? SENTIMENT_COLOR.neutral; label = SENTIMENT_LABEL[hl] ?? "Neutral 😐"; def = SENTIMENT_DEF[hl] ?? ""; }
  else { const s = FACTCHECK_STYLE[part.highlight] ?? FACTCHECK_STYLE["cannot be determined"]; bg = s.bg; accentColor = s.color; label = s.label; borderColor = s.border; def = FACTCHECK_TOOLTIPS[part.highlight] ?? "Click for details."; }
  const isSent = part.mode === "sentiment" && part.isSentence;
  return (
    <>
      <span ref={ref} onMouseEnter={onEnter} onMouseLeave={onLeave} onClick={onClick}
        style={{ background: bg, borderBottom: !isSent ? `2px solid ${borderColor}` : undefined, borderLeft: isSent ? `3px solid ${borderColor}` : undefined, borderRadius: isSent ? "0 2px 2px 0" : 3, padding: isSent ? "1px 4px 1px 5px" : "0 2px", cursor: part.mode === "factcheck" ? "pointer" : "help", display: "inline" }}>
        {part.text}
      </span>
      {!open && <WhiteTooltip label={label} def={def} accentColor={accentColor} anchorRect={rect} visible={hover} />}
      {part.mode === "factcheck" && open && rect && <FactPopup fact={part.fact} anchorRect={rect} onClose={() => setOpen(false)} />}
    </>
  );
}

// ─── Legend pill with hover def ──────────────────────────────────────────────
function LegendPill({ label, bg, color, border, def, count }) {
  const ref = useRef(null); const [tipRect, setTipRect] = useState(null);
  return (
    <div className="relative inline-block">
      <span ref={ref} onMouseEnter={() => ref.current && setTipRect(ref.current.getBoundingClientRect())} onMouseLeave={() => setTipRect(null)}
        className="text-sm font-semibold px-3 py-1 rounded-full cursor-help border inline-flex items-center gap-1"
        style={{ background: bg, color, border: `1px solid ${border ?? color}` }}>
        {label}{count !== undefined && <span className="opacity-60 text-xs ml-0.5">({count})</span>}
      </span>
      {tipRect && createPortal(
        <div style={{ position: "fixed", top: tipRect.top - 46, left: tipRect.left + tipRect.width / 2 - 110, background: "#1f2937", color: "#f3f4f6", padding: "7px 12px", borderRadius: 8, fontSize: 12, maxWidth: 220, zIndex: 9999, pointerEvents: "none", boxShadow: "0 4px 16px rgba(0,0,0,0.28)", textAlign: "center", lineHeight: 1.5 }}>
          {def}
          <div style={{ position: "absolute", bottom: -5, left: "50%", transform: "translateX(-50%)", width: 0, height: 0, borderLeft: "5px solid transparent", borderRight: "5px solid transparent", borderTop: "5px solid #1f2937" }} />
        </div>, document.body
      )}
    </div>
  );
}

function ModeToggle({ mode, setMode, hasPropaganda, hasSentiment, hasFactcheck }) {
  const avail = { propaganda: hasPropaganda, sentiment: hasSentiment, factcheck: hasFactcheck };
  return (
    <div className="flex gap-2 flex-wrap">
      {MODES.map(m => { const disabled = !avail[m.id], active = mode === m.id; return (
        <button key={m.id} onClick={() => !disabled && setMode(m.id)} disabled={disabled}
          className={`text-sm font-semibold px-4 py-1.5 rounded-full border transition-all ${active ? "bg-indigo-600 text-white border-indigo-600 shadow-sm" : disabled ? "bg-gray-50 text-gray-300 border-gray-200 cursor-not-allowed" : "bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600"}`}>
          {m.label}
        </button>
      );})}
    </div>
  );
}

function Legend({ mode, legendItems, hasPropaganda, hasSentiment, hasFactcheck, factcheckResult}) {
  if (mode === "propaganda" && hasPropaganda) return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {legendItems.map(item => <LegendPill key={item.label} label={item.label} bg={item.bg} color={item.color} border={item.bg} def={item.def} />)}
    </div>
  );
  if (mode === "sentiment" && hasSentiment) {
    return (
      <div className="flex flex-wrap gap-1.5 mt-2 items-center">
        {["positive","negative","neutral"].map(key => (
          <LegendPill key={key} label={SENTIMENT_LABEL[key]} bg={SENTIMENT_BG[key]} color={SENTIMENT_COLOR[key]} border={SENTIMENT_BORDER[key]} def={key === "positive" ? "Expresses support or optimism." : key === "negative" ? "Expresses criticism or concern." : "Reports facts without emotional language."} />
        ))}
        <span className="text-xs text-gray-400 italic self-center">Hover for details</span>
      </div>
    );
  }
  if (mode === "factcheck" && hasFactcheck) {
    const facts = Array.isArray(factcheckResult) ? factcheckResult : [];
    const counts = { factual: facts.filter(f => (f.correctness ?? "").toLowerCase() === "factual").length, "cannot be determined": facts.filter(f => (f.correctness ?? "").toLowerCase() === "cannot be determined").length, unfactual: facts.filter(f => (f.correctness ?? "").toLowerCase() === "unfactual").length };
    return (
      <div className="flex flex-wrap gap-1.5 mt-2 items-center">
        {Object.entries(FACTCHECK_STYLE).map(([key, s]) => (
          <LegendPill key={key} label={s.label} bg={s.bg} color={s.color} border={s.border} def={FACTCHECK_DEF[key]} count={counts[key]} />
        ))}
        <span className="text-xs text-gray-400 italic self-center">Click text for details</span>
      </div>
    );
  }
  return null;
}

// ─── Segment builders using shared hlMapToSegs ───────────────────────────────
function buildSentimentSegmentsFromMatches(content, sentimentMatches) {
  if (!sentimentMatches?.length || !content) return null;
  return hlMapToSegs(content, buildHlMap(sentimentMatches.map(m => ({ ...m, hlKey: m.label, mode: "sentiment", isSentence: true }))), e => ({ highlight: e.label, mode: "sentiment", isSentence: true, hlKey: e.hlKey }));
}

function buildFactcheckSegmentsFromMatches(content, factcheckMatches) {
  if (!factcheckMatches?.length || !content) return null;
  return hlMapToSegs(content, buildHlMap(factcheckMatches.map(m => ({ ...m, hlKey: (m.fact.correctness ?? "cannot be determined").toLowerCase(), correctness: (m.fact.correctness ?? "cannot be determined").toLowerCase(), fact: m.fact, mode: "factcheck" }))), e => ({ highlight: e.correctness, mode: "factcheck", fact: e.fact, hlKey: e.hlKey }));
}

function buildPropagandaSegments(content, propagandaResult) {
  if (!propagandaResult?.formatted_result?.length) return null;
  const list = [], seen = new Set();
  for (const item of propagandaResult.formatted_result) {
    const technique = Array.isArray(item) ? item[0] : item.technique;
    const phrase    = Array.isArray(item) ? item[1] : item.phrase;
    if (!technique || !phrase) continue;
    const ctx = findPhraseInContent(phrase, content);
    if (!ctx?.found || seen.has(ctx.match)) continue;
    seen.add(ctx.match); list.push({ technique, match: ctx.match });
  }
  if (!list.length) return null;
  return splitToParagraphs(content).map((para, pi) => {
    const hits = list.map(m => ({ ...m, idx: para.indexOf(m.match) })).filter(m => m.idx !== -1).sort((a, b) => a.idx - b.idx);
    if (!hits.length) return { key: pi, parts: [{ text: para }] };
    const parts = []; let cur = 0;
    for (const m of hits) { if (m.idx > cur) parts.push({ text: para.slice(cur, m.idx) }); parts.push({ text: m.match, highlight: m.technique, mode: "propaganda" }); cur = m.idx + m.match.length; }
    if (cur < para.length) parts.push({ text: para.slice(cur) });
    return { key: pi, parts };
  });
}

// ─── Main component ───────────────────────────────────────────────────────────
const HighlightedArticle = ({ content, propagandaResult, sentimentResult, factcheckResult, factcheckMatches, sentimentMatches }) => {
  const [mode, setMode] = useState("factcheck");

  const sentimentSegments  = useMemo(() => buildSentimentSegmentsFromMatches(content, sentimentMatches),  [content, sentimentMatches]);
  const factcheckSegments  = useMemo(() => buildFactcheckSegmentsFromMatches(content, factcheckMatches),  [content, factcheckMatches]);
  const propagandaSegments = useMemo(() => buildPropagandaSegments(content, propagandaResult),            [content, propagandaResult]);

  const techniqueKeys = useMemo(() => { if (!propagandaResult?.formatted_result?.length) return []; return [...new Set(propagandaResult.formatted_result.map(i => (Array.isArray(i) ? i[0] : i.technique)).filter(Boolean))]; }, [propagandaResult]);
  const legendItems   = getLegendItems(techniqueKeys);
  const hasPropaganda = !!propagandaResult?.formatted_result?.length;
  const hasSentiment  = !!(sentimentResult?.sentence_sentiments?.length);
  const hasFactcheck  = !!(Array.isArray(factcheckResult) && factcheckResult.length);

  useEffect(() => { if (mode === "factcheck" && !hasFactcheck) { if (hasSentiment) setMode("sentiment"); else if (hasPropaganda) setMode("propaganda"); } }, [hasFactcheck, hasSentiment, hasPropaganda, mode]);

  const plainParas = useMemo(() => (content ? splitToParagraphs(content) : []), [content]);

  if (!content) return <p className="text-gray-400 italic">Article content unavailable.</p>;

  const segments = mode === "propaganda" ? propagandaSegments : mode === "sentiment" ? sentimentSegments : factcheckSegments;

  return (
    <div>
      {/* Sticky header */}
      <div style={{ position: "sticky", top: 0, zIndex: 10, background: "#fff", marginLeft: "-1rem", marginRight: "-1rem", paddingLeft: "1rem", paddingRight: "1rem", paddingTop: "0.75rem", paddingBottom: "0.6rem", borderBottom: "1px solid #f3f4f6", marginTop: "-0.75rem" }}>
        <ModeToggle mode={mode} setMode={setMode} hasPropaganda={hasPropaganda} hasSentiment={hasSentiment} hasFactcheck={hasFactcheck} />
        <Legend mode={mode} legendItems={legendItems} hasPropaganda={hasPropaganda} hasSentiment={hasSentiment} hasFactcheck={hasFactcheck} factcheckResult={factcheckResult} sentimentResult={sentimentResult} />
        {((mode === "factcheck" && !hasFactcheck) || (mode === "sentiment" && !hasSentiment) || (mode === "propaganda" && !hasPropaganda)) && (
          <p className="text-sm text-gray-400 italic mt-1.5">{mode === "factcheck" ? "Fact-check data loading…" : mode === "sentiment" ? "Sentiment data loading…" : "No propaganda techniques detected."}</p>
        )}
      </div>
      {/* Article body */}
      <div className="space-y-4 mt-3">
        {(segments ?? plainParas.map((text, key) => ({ key, parts: [{ text }] }))).map(({ key, parts }) => (
          <p key={key} className="leading-relaxed text-base text-gray-800">
            {parts.map((part, i) => part.highlight ? <HighlightSpan key={i} part={part} /> : <span key={i}>{part.text}</span>)}
          </p>
        ))}
      </div>
    </div>
  );
};

export default HighlightedArticle;