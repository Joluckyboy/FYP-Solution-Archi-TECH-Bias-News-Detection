import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import { useLocation, useParams } from "react-router-dom";
import createSSEConnection from "@/hooks/use-SSE";
import get_api from "@/config/config";
import { createPortal } from "react-dom";

import EmotionTab         from "@/components/EmotionTab";
import PropagandaTab      from "@/components/PropagandaTab";
import PoliticalBias      from "@/components/PoliticalBias";
import SentimentTab       from "@/components/SentimentTab";
import FactsCheckTab      from "@/components/FactCheckTab";
import RelatedCoverage    from "@/components/RelatedCoverage";
import TrustSnapshot      from "@/components/TrustSnapshot";
import { HashLoader }     from "react-spinners";
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Separator }      from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import {
  BadgeCheck, Scale, SmilePlus, NewspaperIcon,
  ExternalLink, X, FileText, BookOpen, Sparkles,
} from "lucide-react";
import { findPhraseInContent } from "@/utils/propagandaHighlight";
import {
  buildSentimentMatches, buildFactcheckMatches, getHighlightStyle,
  getLegendItems, splitToParagraphs, buildHlMap, hlMapToSegs,
} from "@/utils/highlightUtils";

import "../index.css";

// ─── Highlight style maps ─────────────────────────────────────────────────────
const SENTIMENT_BG     = { positive: "#dcfce7", negative: "#fee2e2", neutral: "#fef9c3" };
const SENTIMENT_BORDER = { positive: "#4ade80", negative: "#f87171", neutral: "#fbbf24" };
const SENTIMENT_COLOR  = { positive: "#166534", negative: "#991b1b", neutral: "#854d0e" };
const SENTIMENT_LABEL  = { positive: "Positive 😊", negative: "Negative 😟", neutral: "Neutral 😐" };

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

// ─── Popup position ───────────────────────────────────────────────────────────
function computePopupPos(anchorRect, popupW, popupH, margin = 8) {
  const vw = window.innerWidth, vh = window.innerHeight, scrollY = window.scrollY, scrollX = window.scrollX;
  const fitsBelow = vh - anchorRect.bottom >= popupH + margin;
  const fitsAbove = anchorRect.top >= popupH + margin;
  let top, arrowSide;
  if (fitsBelow)      { top = anchorRect.bottom + scrollY + margin; arrowSide = "top"; }
  else if (fitsAbove) { top = anchorRect.top + scrollY - popupH - margin; arrowSide = "bottom"; }
  else                { top = scrollY + margin; arrowSide = "none"; }
  let left = anchorRect.left + scrollX + anchorRect.width / 2 - popupW / 2;
  left = Math.max(scrollX + margin, Math.min(left, scrollX + vw - popupW - margin));
  return { top, left, arrowSide };
}

// ─── Fact popup ───────────────────────────────────────────────────────────────
const FACT_POPUP_STYLE = {
  factual:                { bg: "#f0fdf4", border: "#86efac", color: "#166534", label: "Factual ✅" },
  "cannot be determined": { bg: "#fffbeb", border: "#fcd34d", color: "#92400e", label: "Unclear 🔍" },
  unfactual:              { bg: "#fff1f2", border: "#fda4af", color: "#9f1239", label: "Unfactual ❌" },
};
const showCites = f => {
  if (!f?.citations?.length) return false;
  const e = (f.explanation || "").toLowerCase();
  return !["no sources","no source","sources do not","do not mention","does not mention"].some(p => e.includes(p));
};

function FactPopup({ fact, anchorRect, onClose }) {
  const ref = useRef(null); const [pos, setPos] = useState({});
  useEffect(() => {
    if (!anchorRect || !ref.current) return;
    const w = Math.min(ref.current.offsetWidth || 360, window.innerWidth - 16);
    setPos({ ...computePopupPos(anchorRect, w, ref.current.offsetHeight || 200), width: w });
  }, [anchorRect]);
  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) onClose(); };
    const t = setTimeout(() => document.addEventListener("mousedown", h), 50);
    return () => { clearTimeout(t); document.removeEventListener("mousedown", h); };
  }, [onClose]);
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
          <button onMouseDown={e => { e.stopPropagation(); onClose(); }} className="p-1.5 rounded-lg hover:bg-black/10" style={{ color: style.color, cursor: "pointer" }}><X className="h-4 w-4" /></button>
        </div>
        <div className="px-4 py-3 border-b border-gray-100"><p className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Claim</p><p className="text-sm text-gray-800 leading-relaxed font-medium">{fact?.statement}</p></div>
        <div className="px-4 py-3 border-b border-gray-100"><p className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Explanation</p><p className="text-sm text-gray-600 leading-relaxed italic">{fact?.explanation}</p></div>
        <div className="px-4 py-3">
          <p className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1.5">Sources</p>
          {showCites(fact)
            ? <ul className="space-y-1.5">{fact.citations.map((cit, ci) => <li key={ci} className="flex items-start gap-1.5 text-sm"><span className="font-semibold text-blue-500 shrink-0">[{ci + 1}]</span><a href={cit} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline break-all flex items-center gap-1">{cit.length > 55 ? cit.slice(0, 55) + "…" : cit}<ExternalLink className="h-3 w-3 shrink-0" /></a></li>)}</ul>
            : <p className="text-sm text-gray-400 italic">No verifying sources found</p>}
        </div>
      </div>
    </div>,
    document.body
  );
}

// ─── WhiteTooltip ─────────────────────────────────────────────────────────────
function WhiteTooltip({ label, def, accentColor, anchorRect, visible }) {
  const ref = useRef(null); const [pos, setPos] = useState({ top: 0, left: 0, arrowSide: "top" });
  useEffect(() => { if (!visible || !anchorRect || !ref.current) return; setPos(computePopupPos(anchorRect, ref.current.offsetWidth || 240, ref.current.offsetHeight || 72)); }, [visible, anchorRect]);
  if (!visible) return null;
  const ab = { position: "absolute", width: 0, height: 0, left: "50%", transform: "translateX(-50%)" };
  return createPortal(
    <div ref={ref} style={{ position: "absolute", top: pos.top, left: pos.left, zIndex: 9999, width: 240, pointerEvents: "none" }}>
      {pos.arrowSide === "bottom" && <div style={{ ...ab, bottom: -6, borderTop: "6px solid #e5e7eb", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }} />}
      {pos.arrowSide === "top"    && <div style={{ ...ab, top: -6, borderBottom: "6px solid #e5e7eb", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }} />}
      <div className="text-sm" style={{ background: "#fff", border: "1px solid #e5e7eb", borderLeft: `3px solid ${accentColor}`, borderRadius: 8, padding: "8px 12px", boxShadow: "0 4px 16px rgba(0,0,0,0.10)", lineHeight: 1.5 }}>
        <p style={{ fontWeight: 700, color: accentColor, marginBottom: 3 }}>{label}</p>
        <p style={{ color: "#6b7280", margin: 0 }}>{def}</p>
      </div>
    </div>,
    document.body
  );
}

// ─── HighlightSpan ────────────────────────────────────────────────────────────
function HighlightSpan({ part }) {
  const ref = useRef(null), timer = useRef(null);
  const [hover, setHover] = useState(false), [rect, setRect] = useState(null), [open, setOpen] = useState(false);
  const onEnter = useCallback(() => { clearTimeout(timer.current); if (ref.current) setRect(ref.current.getBoundingClientRect()); setHover(true); }, []);
  const onLeave = useCallback(() => { timer.current = setTimeout(() => setHover(false), 120); }, []);
  useEffect(() => () => clearTimeout(timer.current), []);
  const onClick = useCallback(e => { if (part.mode === "factcheck") { e.stopPropagation(); if (ref.current) setRect(ref.current.getBoundingClientRect()); setOpen(v => !v); setHover(false); } }, [part.mode]);
  let bg, borderColor, accentColor, label, def;
  if (part.mode === "propaganda")   { const s = getHighlightStyle(part.highlight); bg = s.bg; accentColor = s.color ?? "#374151"; label = s.label; def = s.def; borderColor = "transparent"; }
  else if (part.mode === "sentiment") { const hl = part.highlight ?? "neutral"; bg = SENTIMENT_BG[hl] ?? SENTIMENT_BG.neutral; borderColor = SENTIMENT_BORDER[hl] ?? SENTIMENT_BORDER.neutral; accentColor = SENTIMENT_COLOR[hl] ?? SENTIMENT_COLOR.neutral; label = SENTIMENT_LABEL[hl] ?? "Neutral 😐"; def = hl === "positive" ? "Expresses support, optimism, or agreement." : hl === "negative" ? "Expresses criticism, concern, or conflict." : "Reports facts without strong emotional language."; }
  else { const s = FACTCHECK_STYLE[part.highlight] ?? FACTCHECK_STYLE["cannot be determined"]; bg = s.bg; accentColor = s.color; label = s.label; borderColor = s.border; def = FACTCHECK_TOOLTIPS[part.highlight] ?? "Click for details."; }
  const isSent = part.mode === "sentiment";
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

// ─── ArticleBody ──────────────────────────────────────────────────────────────
function ArticleBody({ content, mode, propagandaResult, factcheckMatches, sentimentMatches }) {
  const sentimentSegments = useMemo(() => {
    if (!sentimentMatches?.length || !content) return null;
    return hlMapToSegs(content, buildHlMap(sentimentMatches.map(m => ({ ...m, hlKey: m.label, mode: "sentiment" }))), e => ({ highlight: e.label, mode: "sentiment", hlKey: e.hlKey }));
  }, [content, sentimentMatches]);
  const factcheckSegments = useMemo(() => {
    if (!factcheckMatches?.length || !content) return null;
    return hlMapToSegs(content, buildHlMap(factcheckMatches.map(m => ({ ...m, hlKey: (m.fact.correctness ?? "cannot be determined").toLowerCase(), correctness: (m.fact.correctness ?? "cannot be determined").toLowerCase(), mode: "factcheck" }))), e => ({ highlight: e.correctness, mode: "factcheck", fact: e.fact, hlKey: e.hlKey }));
  }, [content, factcheckMatches]);
  const propagandaSegments = useMemo(() => {
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
  }, [content, propagandaResult]);
  const plainParas = useMemo(() => splitToParagraphs(content), [content]);
  if (!content) return <p className="text-gray-400 italic text-sm">Article content unavailable.</p>;
  const segments   = mode === "propaganda" ? propagandaSegments : mode === "sentiment" ? sentimentSegments : factcheckSegments;
  return (
    <div className="space-y-4">
      {(segments ?? plainParas.map((text, key) => ({ key, parts: [{ text }] }))).map(({ key, parts }) => (
        <p key={key} className="leading-relaxed text-sm text-gray-800">
          {parts.map((part, i) => part.highlight ? <HighlightSpan key={i} part={part} /> : <span key={i}>{part.text}</span>)}
        </p>
      ))}
    </div>
  );
}

// ─── LegendPill ──────────────────────────────────────────────────────────────
function LegendPill({ label, bg, color, border, def, count }) {
  const ref = useRef(null); const [tipRect, setTipRect] = useState(null);
  return (
    <div className="relative inline-block">
      <span ref={ref} onMouseEnter={() => ref.current && setTipRect(ref.current.getBoundingClientRect())} onMouseLeave={() => setTipRect(null)}
        className="text-xs font-semibold px-2.5 py-0.5 rounded-full cursor-help border inline-flex items-center gap-1"
        style={{ background: bg, color, border: `1px solid ${border ?? color}` }}>
        {label}{count !== undefined && <span className="opacity-60">({count})</span>}
      </span>
      {tipRect && createPortal(
        <div className="text-xs leading-relaxed" style={{ position: "fixed", top: tipRect.top - 44, left: tipRect.left + tipRect.width / 2 - 110, background: "#1f2937", color: "#f3f4f6", padding: "7px 12px", borderRadius: 8, maxWidth: 220, zIndex: 9999, pointerEvents: "none", boxShadow: "0 4px 16px rgba(0,0,0,0.28)", textAlign: "center" }}>
          {def}
          <div style={{ position: "absolute", bottom: -5, left: "50%", transform: "translateX(-50%)", width: 0, height: 0, borderLeft: "5px solid transparent", borderRight: "5px solid transparent", borderTop: "5px solid #1f2937" }} />
        </div>,
        document.body
      )}
    </div>
  );
}

// ─── Article Modal ────────────────────────────────────────────────────────────
function ArticleModal({ open, onClose, content, mode, propagandaResult, factcheckMatches, sentimentMatches }) {
  const techniqueKeys = useMemo(() => { if (!propagandaResult?.formatted_result?.length) return []; return [...new Set(propagandaResult.formatted_result.map(i => (Array.isArray(i) ? i[0] : i.technique)).filter(Boolean))]; }, [propagandaResult]);
  const legendItems = getLegendItems(techniqueKeys);
  const modeLabel = mode === "factcheck" ? "✅ Fact-Check" : mode === "sentiment" ? "😐 Sentiment" : "🔴 Propaganda";
  if (!open) return null;
  return createPortal(
    <div className="fixed inset-0 z-[9000] flex">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative ml-auto w-full max-w-xl h-full bg-white shadow-2xl flex flex-col">
        <div className="shrink-0 flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2"><BookOpen className="h-5 w-5 text-indigo-500" /><span className="font-bold text-gray-800 text-lg">Full Article</span></div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100"><X className="h-5 w-5 text-gray-500" /></button>
        </div>
        <div className="shrink-0 px-5 pt-3 pb-2 border-b border-gray-100 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-indigo-600 text-white">{modeLabel}</span>
            <span className="text-xs text-gray-400 italic">highlighting active for this tab</span>
          </div>
          {mode === "factcheck" && (
            <div className="flex flex-wrap gap-1.5 items-center">
              {Object.entries(FACTCHECK_STYLE).map(([key, s]) => (
                <LegendPill key={key} label={s.label} bg={s.bg} color={s.color} border={s.border} def={FACTCHECK_TOOLTIPS[key]} />
              ))}
              <span className="text-xs text-gray-400 italic">Click text for details</span>
            </div>
          )}
          {mode === "sentiment" && (
            <div className="flex flex-wrap gap-1.5 items-center">
              {["positive","negative","neutral"].map(key => (
                <LegendPill key={key} label={SENTIMENT_LABEL[key]} bg={SENTIMENT_BG[key]} color={SENTIMENT_COLOR[key]} border={SENTIMENT_BORDER[key]}
                  def={key === "positive" ? "Expresses support or optimism." : key === "negative" ? "Expresses criticism or concern." : "Reports facts without emotional language."} />
              ))}
              <span className="text-xs text-gray-400 italic">Hover for details</span>
            </div>
          )}
          {mode === "propaganda" && legendItems.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {legendItems.map(item => <LegendPill key={item.label} label={item.label} bg={item.bg} color={item.color} def={item.def} />)}
            </div>
          )}
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">
          <ArticleBody content={content} mode={mode} propagandaResult={propagandaResult} factcheckMatches={factcheckMatches} sentimentMatches={sentimentMatches} />
        </div>
      </div>
    </div>,
    document.body
  );
}

// ─── FAB ─────────────────────────────────────────────────────────────────────
const FAB_TABS = new Set(["facts", "sentiment", "propaganda"]);

function ViewArticleFAB({ onClick, disabled, visible }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { if (visible) { const t = setTimeout(() => setMounted(true), 60); return () => clearTimeout(t); } else { setMounted(false); } }, [visible]);
  if (!visible) return null;
  return createPortal(
    <button onClick={onClick} disabled={disabled} aria-label="View Full Article" className="text-sm"
      style={{ position: "fixed", bottom: 24, right: 20, zIndex: 8000, display: "flex", alignItems: "center", gap: 8, paddingLeft: 18, paddingRight: 18, paddingTop: 12, paddingBottom: 12, borderRadius: 40, background: disabled ? "#c7d2fe" : "linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)", color: "#fff", fontWeight: 700, border: "none", cursor: disabled ? "not-allowed" : "pointer", boxShadow: disabled ? "none" : "0 4px 20px rgba(99,102,241,0.45), 0 2px 8px rgba(0,0,0,0.15)", transform: mounted ? "translateY(0) scale(1)" : "translateY(16px) scale(0.92)", opacity: mounted ? 1 : 0, transition: "transform 0.22s cubic-bezier(0.34,1.56,0.64,1), opacity 0.18s ease", whiteSpace: "nowrap" }}>
      <FileText style={{ width: 16, height: 16, flexShrink: 0 }} />
      View Full Article
    </button>,
    document.body
  );
}

// ─── ViewArticleNudge — contextual banner inside each analysis tab ────────────
// Shows a soft hint so users know they can open the highlighted article view.
// Tab-specific copy explains what they'll see when they open it.
const NUDGE_CONFIG = {
  facts: {
    bg: "#eff6ff",
    border: "#bfdbfe",
    iconColor: "#3b82f6",
    text: "See exactly which sentences were fact-checked — highlighted directly in the article.",
    cta: "Open highlighted article →",
  },
  sentiment: {
    bg: "#fdf4ff",
    border: "#e9d5ff",
    iconColor: "#9333ea",
    text: "Explore positive, negative and neutral language highlighted sentence-by-sentence in the full text.",
    cta: "Open highlighted article →",
  },
  propaganda: {
    bg: "#fff7ed",
    border: "#fed7aa",
    iconColor: "#f97316",
    text: "See every influence technique flagged and highlighted in context within the original article.",
    cta: "Open highlighted article →",
  },
};

function ViewArticleNudge({ tab, onOpen, hasContent }) {
  const cfg = NUDGE_CONFIG[tab];
  if (!cfg || !hasContent) return null;
  return (
    <div
      className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl px-4 py-3 mb-4 border"
      style={{ background: cfg.bg, borderColor: cfg.border }}
    >
      <div className="flex items-start gap-2.5 min-w-0 flex-1">
        <Sparkles style={{ color: cfg.iconColor, width: 16, height: 16, flexShrink: 0, marginTop: 2 }} />
        <p className="text-sm text-gray-600 leading-snug">{cfg.text}</p>
      </div>
      <button
        onClick={onOpen}
        className="shrink-0 text-sm font-semibold rounded-lg px-4 py-2 transition whitespace-nowrap self-start sm:self-auto"
        style={{ color: cfg.iconColor, background: "rgba(255,255,255,0.95)", border: `1px solid ${cfg.border}` }}
      >
        {cfg.cta}
      </button>
    </div>
  );
}

// ─── Main ResultsPage ─────────────────────────────────────────────────────────
const ResultsPage = () => {
  const location = useLocation();
  const { id }   = useParams();
  const [data,         setData]         = useState(location.state?.data || null);
  const [API_URL,      setAPI_URL]      = useState(null);
  const [badgeUpdated, setBadgeUpdated] = useState(false);
  const [modalOpen,    setModalOpen]    = useState(false);
  const [activeTab,    setActiveTab]    = useState("facts");
  const summaryRegenTriggeredRef = useRef(new Set());

  useEffect(() => {
    get_api().then(setAPI_URL);
    window.addEventListener("resize", () => {});
    return () => window.removeEventListener("resize", () => {});
  }, []);
  useEffect(() => { if (!API_URL || !id) return; const ev = createSSEConnection(API_URL, id, setData); return () => ev?.close(); }, [API_URL, id]);
  useEffect(() => {
    if (!API_URL || !data?.url) return;
    const hasSummary = data.data_summary && Object.keys(data.data_summary).length > 0;
    const key = data.id || data.url;
    if (!key) return;
    if (!hasSummary && data.sentiment_result && data.emotion_result && data.propaganda_result && !summaryRegenTriggeredRef.current.has(key)) {
      summaryRegenTriggeredRef.current.add(key);
      fetch(`${API_URL}/application/new_query`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: data.url, force: false }) }).catch(() => {});
    }
  }, [API_URL, data]);
  useEffect(() => {
    if (!badgeUpdated && data?.propaganda_result?.propaganda_probability !== undefined && typeof chrome !== "undefined" && chrome.runtime?.id) {
      chrome.runtime.sendMessage({ action: "propagandaResultReceived", propagandaProbability: data.propaganda_result.propaganda_probability, url: data.url || location.state?.articleUrl });
      setBadgeUpdated(true);
    }
  }, [data?.propaganda_result, badgeUpdated, location.state?.articleUrl, data?.url]);

  const factcheckMatches = useMemo(() => buildFactcheckMatches(data?.content, data?.factcheck_result), [data?.content, data?.factcheck_result]);
  const sentimentMatches = useMemo(() => buildSentimentMatches(data?.content, data?.sentiment_result), [data?.content, data?.sentiment_result]);
  const modalMode = activeTab === "sentiment" ? "sentiment" : activeTab === "propaganda" ? "propaganda" : "factcheck";
  const fabVisible = FAB_TABS.has(activeTab) && !modalOpen && !!data?.content;

  if (!data) return (
    <div className="app-container flex items-center justify-center">
      <div className="text-center"><h1>Loading...</h1><br /><HashLoader color="#1E5EDD" size={50} /></div>
    </div>
  );

  const domain = (() => { try { return new URL(data.url).hostname.replace("www.", ""); } catch { return data.url; } })();
  const sourceLabel = data?.source || domain;
  const faviconUrl = domain
    ? `https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${domain}&size=64`
    : null;
  const emotionSummaryText       = data?.data_summary?.emotion_summary        || "No emotion summary available";
  const propagandaSummaryText    = data?.data_summary?.propaganda_summary     || "No propaganda summary available";
  const sentimentSummaryText     = data?.data_summary?.sentiment_summary      || "No sentiment summary available";
  const politicalBiasSummaryText = data?.data_summary?.political_bias_summary || "No political bias summary available";
  const openModal = () => setModalOpen(true);

  return (
    <div className="app-container">
      <ViewArticleFAB visible={fabVisible} disabled={!data?.content} onClick={openModal} />
      <ArticleModal open={modalOpen} onClose={() => setModalOpen(false)} content={data?.content} mode={modalMode}
        propagandaResult={data?.propaganda_result} factcheckMatches={factcheckMatches} sentimentMatches={sentimentMatches}
        factcheckResult={data?.factcheck_result} sentimentResult={data?.sentiment_result} />

      {/* ── Article title card ───────────────────────────────────────── */}
      <Card className="mb-6 staggered-slide-in overflow-hidden">
        <CardHeader className="pb-4">
          {/* Source row */}
          <div className="flex items-center gap-3 mb-3">
            {faviconUrl && (
              <img src={faviconUrl} alt={sourceLabel}
                className="rounded-lg border border-slate-200 bg-white shadow-sm"
                style={{ width: 36, height: 36, objectFit: "contain", flexShrink: 0 }}
                loading="lazy" />
            )}
            <div className="flex flex-col">
              <span className="text-base font-bold text-slate-700 leading-tight">{sourceLabel}</span>
              <span className="text-xs text-slate-400 font-normal">{domain}</span>
            </div>
          </div>
          {/* Title + button */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <CardTitle className="text-xl font-bold leading-snug sm:text-xl md:text-2xl min-w-0 flex-1">
              {data?.title ?? "No title available"}
            </CardTitle>
            <a href={data?.url} target="_blank" rel="noopener noreferrer"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-100 self-start">
              <ExternalLink className="h-4 w-4" />
              Open Article
            </a>
          </div>
        </CardHeader>
      </Card>

      {/* ── Trust snapshot ───────────────────────────────────────────── */}
      <div className="mb-6">
        <TrustSnapshot data={data} apiUrl={API_URL} />
      </div>

      {/* ── Analysis Tabs ────────────────────────────────────────────── */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full slide-in-right">
       <TabsList className="hidden md:grid w-full grid-cols-5 gap-1 shadow mb-4">
        <TabsTrigger value="facts">Facts</TabsTrigger>
        <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
        <TabsTrigger value="emotion">Emotion</TabsTrigger>
        <TabsTrigger value="propaganda">Propaganda</TabsTrigger>
        <TabsTrigger value="bias">Bias</TabsTrigger>
      </TabsList>
      <TabsList className="flex md:hidden w-full shadow mb-4">
        <TabsTrigger value="facts">Facts</TabsTrigger>
        <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
        <TabsTrigger value="emotion">Emotion</TabsTrigger>
        <TabsTrigger value="propaganda">Propaganda</TabsTrigger>
        <TabsTrigger value="bias">Bias</TabsTrigger>
      </TabsList>

        {/* ══ FACTS ══ */}
        <TabsContent value="facts">
          <Card className="p-4">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <BadgeCheck className="h-10 w-10" />
                <CardTitle className="text-2xl md:text-3xl">Fact-Checking</CardTitle>
              </div>
              <CardDescription>Key claims from the article, checked against available sources.</CardDescription>
            </CardHeader>

            {/* Contextual nudge */}
            <div className="mt-2 mx-4">
              <ViewArticleNudge tab="facts" onOpen={openModal} hasContent={!!data?.content} />
            </div>

            <div className="mt-1 ml-4 mr-4 rounded-md border p-3 bg-white">
              <p className="mb-2 ml-4 mr-4 font-medium text-sm">Legend:</p>
              <div className="flex flex-col space-y-2">
                <div className="flex items-center"><div className="w-4 h-4 rounded mr-2 bg-teal-100" /><span className="text-sm"><b>Factual</b> — Verified with reliable sources</span></div>
                <div className="flex items-center"><div className="w-4 h-4 rounded mr-2 bg-amber-100" /><span className="text-sm"><b>Cannot be determined</b> — Insufficient evidence</span></div>
                <div className="flex items-center"><div className="w-4 h-4 rounded mr-2 bg-rose-100" /><span className="text-sm"><b>Unfactual</b> — Contradicts reliable evidence</span></div>
              </div>
            </div>
            <Separator className="mt-4 mb-4" />
            <CardContent>
              <FactsCheckTab facts={data.factcheck_result} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ══ SENTIMENT ══ */}
        <TabsContent value="sentiment">
          <Card className="p-4">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <BadgeCheck className="h-10 w-10" />
                <CardTitle className="text-2xl md:text-3xl">Sentiment Analysis</CardTitle>
              </div>
              <CardDescription>Measures whether the language used is positive, negative, or neutral.</CardDescription>
              <Accordion type="single" collapsible className="w-full mt-2">
                <AccordionItem value="s-sum">
                  <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                  <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{sentimentSummaryText}</AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardHeader>

            {/* Contextual nudge */}
            <div className="mt-2 mx-4">
              <ViewArticleNudge tab="sentiment" onOpen={openModal} hasContent={!!data?.content} />
            </div>

            <Separator className="mb-4" />
            <CardContent>
              <SentimentTab sentimentResult={data.sentiment_result} sentimentSummaryText={sentimentSummaryText} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ══ EMOTION ══ */}
        <TabsContent value="emotion">
          <Card className="p-4">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <SmilePlus className="h-10 w-10" />
                <CardTitle className="text-2xl md:text-3xl">Emotion Analysis</CardTitle>
              </div>
              <CardDescription>Goes deeper than positive/negative — detects emotions like fear, approval, or anger.</CardDescription>
              <Accordion type="single" collapsible className="w-full mt-2">
                <AccordionItem value="e-sum">
                  <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                  <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{emotionSummaryText}</AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardHeader>
            <Separator className="mb-4" />
            {!data.emotion_result || !Object.keys(data.emotion_result).length ? (
              <CardContent><div className="text-center flex flex-col items-center py-8"><br />Analysis in progress<br /><br /><HashLoader color="#1E5EDD" size={50} /></div></CardContent>
            ) : (
              <CardContent>
                {data.emotion_result?.weighted_avg ? <EmotionTab emotionResult={data.emotion_result} /> : <p className="text-gray-500 text-sm">No emotion data available.</p>}
              </CardContent>
            )}
          </Card>
        </TabsContent>

        {/* ══ PROPAGANDA ══ */}
        <TabsContent value="propaganda">
          <Card className="p-4">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Scale className="h-10 w-10" />
                <CardTitle className="text-2xl md:text-3xl">Propaganda Analysis</CardTitle>
              </div>
              <CardDescription>Detects language techniques commonly used to influence readers.</CardDescription>
              <Accordion type="single" collapsible className="w-full mt-2">
                <AccordionItem value="p-sum">
                  <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                  <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{propagandaSummaryText}</AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardHeader>

            {/* Contextual nudge */}
            <div className="mt-2 mx-4">
              <ViewArticleNudge tab="propaganda" onOpen={openModal} hasContent={!!data?.content} />
            </div>

            <Separator className="mb-4" />
            {!data.propaganda_result || !Object.keys(data.propaganda_result).length ? (
              <CardContent><div className="text-center flex flex-col items-center py-8"><br />Analysis in progress<br /><br /><HashLoader color="#1E5EDD" size={50} /></div></CardContent>
            ) : (
              <CardContent>
                <PropagandaTab propScore={data.propaganda_result} articleContent={data.content} />
              </CardContent>
            )}
          </Card>
        </TabsContent>

        {/* ══ POLITICAL BIAS ══ */}
        <TabsContent value="bias">
          <Card className="p-4">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Scale className="h-10 w-10" />
                <CardTitle className="text-2xl md:text-3xl">Political Bias</CardTitle>
              </div>
              <CardDescription>Analyses the political leaning and topic framing of the article.</CardDescription>
              <Accordion type="single" collapsible className="w-full mt-2">
                <AccordionItem value="b-sum">
                  <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                  <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{politicalBiasSummaryText}</AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardHeader>
            <Separator className="mb-4" />
            <CardContent>
              <PoliticalBias politicalBiasResult={data.political_bias_result} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* ── Related Coverage ─────────────────────────────────────────── */}
      <Card className="p-4 mt-6">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <NewspaperIcon strokeWidth={1.5} className="h-10 w-10" />
            <CardTitle className="text-2xl md:text-3xl">Related Coverage</CardTitle>
          </div>
          <CardDescription>Same story covered by other outlets — click <strong>Compare</strong> for a side-by-side analysis.</CardDescription>
        </CardHeader>
        <Separator className="mb-4" />
        <CardContent>
          {data?.url && API_URL
            ? <RelatedCoverage articleUrl={data.url} analysedArticle={data} apiUrl={API_URL} hideHeader />
            : <div className="text-center py-6 text-slate-400">Loading…</div>}
        </CardContent>
      </Card>
    </div>
  );
};

export default ResultsPage;