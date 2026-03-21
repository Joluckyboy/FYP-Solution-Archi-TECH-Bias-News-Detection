import { useMemo, useState, useCallback, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { findPhraseInContent } from "@/utils/propagandaHighlight";
import { getHighlightStyle, getLegendItems } from "@/utils/highlightPropaganda";

// ─── Build highlight segments (unchanged from original) ──────────────────────

function buildSegments(content, propagandaResult) {
  if (!propagandaResult?.formatted_result?.length) return null;

  const matchList  = [];
  const seenMatches = new Set();

  for (const item of propagandaResult.formatted_result) {
    const technique = Array.isArray(item) ? item[0] : item.technique;
    const phrase    = Array.isArray(item) ? item[1] : item.phrase;
    if (!technique || !phrase) continue;

    const ctx = findPhraseInContent(phrase, content);
    if (!ctx?.found) continue;
    if (seenMatches.has(ctx.match)) continue;

    seenMatches.add(ctx.match);
    matchList.push({ technique, match: ctx.match });
  }

  if (!matchList.length) return null;

  let paragraphs = content.split(/\n\n+/).filter(p => p.trim());
  if (paragraphs.length <= 1) {
    const flat         = content.replace(/\n\n+/g, " ");
    const allSentences = flat
      .split(/(?<=[.!?""''])\s+(?=[A-Z"''])/g)
      .map(s => s.trim())
      .filter(Boolean);
    paragraphs = [];
    for (let i = 0; i < allSentences.length; i += 3) {
      paragraphs.push(allSentences.slice(i, i + 3).join(" "));
    }
  }

  return paragraphs.map((para, pi) => {
    const paraMatches = matchList
      .map(m => ({ ...m, idx: para.indexOf(m.match) }))
      .filter(m => m.idx !== -1)
      .sort((a, b) => a.idx - b.idx);

    if (!paraMatches.length) {
      return { key: pi, parts: [{ text: para, highlight: null }] };
    }

    const parts = [];
    let cursor  = 0;
    for (const m of paraMatches) {
      if (m.idx > cursor) parts.push({ text: para.slice(cursor, m.idx), highlight: null });
      parts.push({ text: m.match, highlight: m.technique });
      cursor = m.idx + m.match.length;
    }
    if (cursor < para.length) parts.push({ text: para.slice(cursor), highlight: null });

    return { key: pi, parts };
  });
}

// ─── Smart floating tooltip ───────────────────────────────────────────────────
// Renders into document.body via portal so it's never clipped by
// overflow:hidden on ScrollArea or Card containers.

function FloatingTooltip({ label, def, anchorRect, visible }) {
  const tooltipRef = useRef(null);
  const [pos, setPos] = useState({ top: 0, left: 0, above: false });

  useEffect(() => {
    if (!visible || !anchorRect || !tooltipRef.current) return;

    const tt       = tooltipRef.current;
    const ttW      = tt.offsetWidth  || 220;
    const ttH      = tt.offsetHeight || 80;
    const vw       = window.innerWidth;
    const vh       = window.innerHeight;
    const scrollY  = window.scrollY;
    const scrollX  = window.scrollX;

    // Prefer below, flip above if not enough space
    const spaceBelow = vh - (anchorRect.bottom - scrollY);
    const above      = spaceBelow < ttH + 12;

    let top  = above
      ? anchorRect.top  + scrollY - ttH - 8
      : anchorRect.bottom + scrollY + 8;

    // Horizontally centre on anchor, clamp to viewport
    let left = anchorRect.left + scrollX + anchorRect.width / 2 - ttW / 2;
    left = Math.max(8, Math.min(left, vw + scrollX - ttW - 8));

    setPos({ top, left, above });
  }, [visible, anchorRect]);

  if (!visible) return null;

  return createPortal(
    <div
      ref={tooltipRef}
      style={{
        position:  "absolute",
        top:       pos.top,
        left:      pos.left,
        zIndex:    9999,
        width:     220,
        pointerEvents: "none",
      }}
    >
      {/* arrow */}
      <div style={{
        position:   "absolute",
        left:       "50%",
        transform:  "translateX(-50%)",
        ...(pos.above
          ? { bottom: -6, borderTop: "6px solid #1f2937", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }
          : { top:    -6, borderBottom: "6px solid #1f2937", borderLeft: "6px solid transparent", borderRight: "6px solid transparent" }),
        width: 0, height: 0,
      }} />
      <div style={{
        background:   "#1f2937",
        color:        "#f9fafb",
        borderRadius: 8,
        padding:      "8px 12px",
        boxShadow:    "0 4px 16px rgba(0,0,0,0.25)",
        fontSize:     13,
        lineHeight:   1.45,
      }}>
        <p style={{ fontWeight: 600, marginBottom: 4, color: "#fff" }}>{label}</p>
        <p style={{ color: "#d1d5db", margin: 0 }}>{def}</p>
      </div>
    </div>,
    document.body
  );
}

// ─── Single highlighted span with floating tooltip ───────────────────────────

function HighlightedPart({ part }) {
  const style        = getHighlightStyle(part.highlight);
  const spanRef      = useRef(null);
  const [show, setShow]       = useState(false);
  const [rect, setRect]       = useState(null);
  const hideTimerRef = useRef(null);

  const handleMouseEnter = useCallback(() => {
    clearTimeout(hideTimerRef.current);
    if (spanRef.current) {
      setRect(spanRef.current.getBoundingClientRect());
    }
    setShow(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    // Small delay so mouse can move to tooltip without flicker
    hideTimerRef.current = setTimeout(() => setShow(false), 120);
  }, []);

  // Cleanup timer on unmount
  useEffect(() => () => clearTimeout(hideTimerRef.current), []);

  return (
    <>
      <span
        ref={spanRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{
          background:    style.bg,
          color:         "inherit",
          borderRadius:  3,
          padding:       "0 2px",
          cursor:        "help",
          position:      "relative",
        }}
      >
        {part.text}
      </span>
      <FloatingTooltip
        label={style.label}
        def={style.def}
        anchorRect={rect}
        visible={show}
      />
    </>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

const HighlightedArticle = ({ content, propagandaResult }) => {
  const segments = useMemo(
    () => buildSegments(content, propagandaResult),
    [content, propagandaResult]
  );

  const techniqueKeys = useMemo(() => {
    if (!propagandaResult?.formatted_result?.length) return [];
    return [...new Set(
      propagandaResult.formatted_result
        .map(item => Array.isArray(item) ? item[0] : item.technique)
        .filter(Boolean)
    )];
  }, [propagandaResult]);

  const legendItems = getLegendItems(techniqueKeys);

  if (!content) {
    return (
      <p className="text-gray-400 italic text-sm">Full article content is unavailable.</p>
    );
  }

  // Propaganda not yet loaded — show plain paragraphs
  if (!segments) {
    return (
      <div className="space-y-3">
        {content.split(/\n\n+/).filter(p => p.trim()).map((p, i) => (
          <p key={i} className="leading-relaxed text-sm">{p}</p>
        ))}
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Sticky legend */}
      {legendItems.length > 0 && (
        <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm flex flex-wrap gap-1.5 py-2 mb-3 border-b border-gray-100">
          {legendItems.map(item => (
            <span
              key={item.label}
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{ background: item.bg, color: item.color }}
            >
              {item.label}
            </span>
          ))}
        </div>
      )}

      {/* Article body */}
      <div className="space-y-3">
        {segments.map(({ key, parts }) => (
          <p key={key} className="leading-relaxed text-sm">
            {parts.map((part, i) => {
              if (!part.highlight) return <span key={i}>{part.text}</span>;
              return <HighlightedPart key={i} part={part} />;
            })}
          </p>
        ))}
      </div>
    </div>
  );
};

export default HighlightedArticle;