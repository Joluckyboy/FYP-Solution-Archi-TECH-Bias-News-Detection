import { useRef, useEffect, useState, useCallback } from "react";
import {
  X, GitCompareArrows, ExternalLink,
  TrendingUp, TrendingDown, Minus, Loader2,
} from "lucide-react";

// ─── Bias config ──────────────────────────────────────────────────────────────

const BIAS_STYLE = {
  left:            { label: "Left",          color: "#1d4ed8", bg: "#dbeafe", border: "#93c5fd" },
  "leaning-left":  { label: "Leaning Left",  color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe" },
  "leaning left":  { label: "Leaning Left",  color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe" },
  center:          { label: "Center",        color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe" },
  centre:          { label: "Center",        color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe" },
  neutral:         { label: "Center",        color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe" },
  "leaning-right": { label: "Leaning Right", color: "#dc2626", bg: "#fff1f2", border: "#fecaca" },
  "leaning right": { label: "Leaning Right", color: "#dc2626", bg: "#fff1f2", border: "#fecaca" },
  right:           { label: "Right",         color: "#b91c1c", bg: "#fee2e2", border: "#fca5a5" },
};

const BIAS_SPECTRUM = ["left", "leaning-left", "center", "leaning-right", "right"];

function getBias(raw) {
  const key = (raw || "").toLowerCase().trim().replace(/_/g, "-");
  return BIAS_STYLE[key] ?? { label: raw || "Unknown", color: "#64748b", bg: "#f8fafc", border: "#e2e8f0" };
}

function biasPosition(raw) {
  const key = (raw || "").toLowerCase().trim().replace(/_/g, "-");
  const idx = BIAS_SPECTRUM.indexOf(key);
  return idx === -1 ? 2 : idx;
}

// ─── Analysis helpers ─────────────────────────────────────────────────────────

function dominantSentiment(r) {
  if (!r || !Object.keys(r).length) return null;
  const { positive = 0, negative = 0, neutral = 0 } = r;
  if (positive >= negative && positive >= neutral) return { label: "Positive", value: positive, color: "#16a34a", Icon: TrendingUp };
  if (negative >= positive && negative >= neutral) return { label: "Negative", value: negative, color: "#dc2626", Icon: TrendingDown };
  return { label: "Neutral", value: neutral, color: "#64748b", Icon: Minus };
}

function dominantEmotion(r) {
  if (!r?.dominant_emotion) return null;
  const em = r.dominant_emotion;
  return `${em.charAt(0).toUpperCase() + em.slice(1)} (${Math.round((r.dominant_score ?? 0) * 100)}%)`;
}

function propagandaScore(r) {
  if (r?.propaganda_probability == null) return null;
  return Math.round(r.propaganda_probability * 100);
}

function factcheckSummary(r) {
  if (!Array.isArray(r) || !r.length) return null;
  const total     = r.length;
  const factual   = r.filter(f => (f.correctness || "").toLowerCase() === "factual").length;
  const unfactual = r.filter(f => (f.correctness || "").toLowerCase() === "unfactual").length;
  return { total, factual, unfactual, unclear: total - factual - unfactual };
}

function isAnalysisComplete(data) {
  return !!(
    data &&
    data.sentiment_result   && Object.keys(data.sentiment_result).length &&
    data.emotion_result     && Object.keys(data.emotion_result).length &&
    data.propaganda_result  && data.propaganda_result.propaganda_probability != null &&
    Array.isArray(data.factcheck_result) && data.factcheck_result.length > 0 &&
    data.political_bias_result && data.political_bias_result.rating
  );
}

// ─── Key Difference ───────────────────────────────────────────────────────────

function buildKeyDifference(a, b) {
  const diffs = [];

  const aBiasRaw = a?.political_bias_result?.rating || "";
  const bBiasRaw = b?.political_bias_result?.rating || "";
  const gap = Math.abs(biasPosition(aBiasRaw) - biasPosition(bBiasRaw));
  if (gap >= 2) {
    diffs.push(`These articles sit at opposite ends of the political spectrum — ${getBias(aBiasRaw).label} vs ${getBias(bBiasRaw).label}.`);
  } else if (gap === 1) {
    diffs.push(`The articles lean in slightly different political directions.`);
  }

  const aSent = dominantSentiment(a?.sentiment_result);
  const bSent = dominantSentiment(b?.sentiment_result);
  if (aSent && bSent && aSent.label !== bSent.label) {
    diffs.push(`Tone differs: this article is ${aSent.label.toLowerCase()} while the related is ${bSent.label.toLowerCase()}.`);
  }

  const aProp = propagandaScore(a?.propaganda_result);
  const bProp = propagandaScore(b?.propaganda_result);
  if (aProp != null && bProp != null && Math.abs(aProp - bProp) >= 20) {
    const higher = aProp > bProp ? "this article" : "the related article";
    diffs.push(`${higher.charAt(0).toUpperCase() + higher.slice(1)} has notably higher influence language (${Math.max(aProp, bProp)}% vs ${Math.min(aProp, bProp)}%).`);
  }

  return diffs.length === 0
    ? "Both articles cover the same story. Compare the detailed metrics below for framing differences."
    : diffs.join(" ");
}

// ─── Metric block ─────────────────────────────────────────────────────────────

function MetricBlock({ label, children }) {
  return (
    <div className="rounded-lg px-3 py-2.5 bg-slate-50 border border-slate-100">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">{label}</p>
      {children}
    </div>
  );
}

// ─── Article column ───────────────────────────────────────────────────────────

function ArticleColumn({ label, data, isAnalysed, loading, loadingMessage }) {
  const biasRaw = data?.political_bias_result?.rating || "";
  const bias    = getBias(biasRaw);
  const sent    = dominantSentiment(data?.sentiment_result);
  const emotion = dominantEmotion(data?.emotion_result);
  const prop    = propagandaScore(data?.propaganda_result);
  const facts   = factcheckSummary(data?.factcheck_result);

  const domain = (() => {
    try { return new URL(data?.url || "").hostname.replace("www.", ""); }
    catch { return data?.source || ""; }
  })();

  const tagStyle = isAnalysed
    ? { background: "#f0fdf4", color: "#166534", border: "1px solid #bbf7d0" }
    : { background: "#faf5ff", color: "#5b21b6", border: "1px solid #ddd6fe" };

  return (
    <div className="flex flex-col h-full">
      <div
        className="text-xs font-bold uppercase tracking-widest px-3 py-1.5 rounded-full self-start mb-3"
        style={tagStyle}
      >
        {label}
      </div>

      {/* Source + title */}
      <div className="mb-4">
        <div className="flex items-center gap-1.5 mb-1.5">
          <img
            src={`https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${domain}&size=32`}
            alt={data?.source || domain}
            className="h-4 w-4 rounded-full flex-shrink-0"
            onError={(e) => { e.target.style.display = "none"; }}
          />
          <span className="text-xs font-semibold text-slate-500">{data?.source || domain}</span>
        </div>
        <a
          href={data?.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-semibold text-slate-800 hover:text-indigo-600 leading-snug transition-colors"
        >
          {data?.title}
          <ExternalLink className="inline ml-1 h-3 w-3 opacity-40" />
        </a>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-10 gap-3 text-slate-400">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
          <p className="text-xs text-center leading-relaxed max-w-[200px]">
            {loadingMessage || "Fetching analysis…"}
          </p>
        </div>
      )}

      {/* Metrics */}
      {!loading && data && (
        <div className="grid grid-cols-1 gap-2 flex-1">

          {/* Political Bias */}
          <div
            className="rounded-lg px-3 py-2.5"
            style={{ background: bias.bg, border: `1px solid ${bias.border}` }}
          >
            <p className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: bias.color, opacity: 0.7 }}>
              Political Bias
            </p>
            {bias.label !== "Unknown"
              ? <p className="text-sm font-bold" style={{ color: bias.color }}>{bias.label}</p>
              : <p className="text-xs text-slate-400 italic">Not available yet</p>}
          </div>

          {/* Sentiment */}
          <MetricBlock label="Sentiment Tone">
            {sent ? (
              <div className="flex items-center gap-1.5">
                <sent.Icon className="h-3.5 w-3.5 flex-shrink-0" style={{ color: sent.color }} />
                <span className="text-sm font-semibold" style={{ color: sent.color }}>
                  {sent.label}
                  <span className="text-xs font-normal text-slate-400 ml-1">({Math.round(sent.value * 100)}%)</span>
                </span>
              </div>
            ) : <p className="text-xs text-slate-400 italic">Not available yet</p>}
          </MetricBlock>

          {/* Emotion */}
          <MetricBlock label="Dominant Emotion">
            {emotion
              ? <p className="text-sm font-semibold text-slate-700">{emotion}</p>
              : <p className="text-xs text-slate-400 italic">Not available yet</p>}
          </MetricBlock>

          {/* Propaganda */}
          <MetricBlock label="Influence Language Score">
            {prop != null ? (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold text-slate-700">{prop}%</span>
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                    prop >= 65 ? "bg-red-100 text-red-700"
                    : prop >= 35 ? "bg-amber-100 text-amber-700"
                    : "bg-green-100 text-green-700"
                  }`}>
                    {prop >= 65 ? "High" : prop >= 35 ? "Moderate" : "Low"}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      prop >= 65 ? "bg-red-400" : prop >= 35 ? "bg-amber-400" : "bg-green-400"
                    }`}
                    style={{ width: `${prop}%` }}
                  />
                </div>
              </div>
            ) : <p className="text-xs text-slate-400 italic">Not available yet</p>}
          </MetricBlock>

          {/* Fact-check */}
          <MetricBlock label="Fact-Check Summary">
            {facts ? (
              <div className="flex flex-wrap gap-1.5">
                <span className="text-[11px] bg-teal-100 text-teal-700 px-2 py-0.5 rounded-full font-semibold">
                  ✅ {facts.factual} verified
                </span>
                <span className="text-[11px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-semibold">
                  🔍 {facts.unclear} unclear
                </span>
                {facts.unfactual > 0 && (
                  <span className="text-[11px] bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full font-semibold">
                    ❌ {facts.unfactual} false
                  </span>
                )}
              </div>
            ) : <p className="text-xs text-slate-400 italic">Not available yet</p>}
          </MetricBlock>

          {/* Article summary */}
          {(data?.summarise_result || data?.summary) && (
            <MetricBlock label="Summary">
              <p className="text-xs text-slate-600 leading-relaxed line-clamp-4">
                {data?.summarise_result || data?.summary}
              </p>
            </MetricBlock>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

const InlineComparison = ({ analysedArticle, relatedArticle, apiUrl, onClose }) => {
  const panelRef      = useRef(null);
  const esRef         = useRef(null);

  const [relatedData,    setRelatedData]    = useState(null);
  const [loadingState,   setLoadingState]   = useState("idle");
  const [loadingMessage, setLoadingMessage] = useState("");

  // Scroll into view on open
  useEffect(() => {
    if (panelRef.current) {
      panelRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [relatedArticle?.url]);

  // Fetch full analysis for the related article via the same pipeline as the main article
  const fetchRelatedAnalysis = useCallback(async (articleUrl) => {
    if (!apiUrl || !articleUrl) return;

    if (esRef.current) { esRef.current.close(); esRef.current = null; }

    try {
      setLoadingState("submitting");
      setLoadingMessage("Submitting article for analysis…");

      // POST to new_query — returns immediately with whatever is already in DB,
      // and kicks off background analysis for any missing fields
      const resp = await fetch(`${apiUrl}/application/new_query`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ url: articleUrl, background: true, force: false }),
      });

      if (!resp.ok) throw new Error(`Submit failed: ${resp.status}`);

      const initialData = await resp.json();

      // Already complete — render immediately
      if (isAnalysisComplete(initialData)) {
        setRelatedData(initialData);
        setLoadingState("done");
        return;
      }

      // Show partial data while streaming the rest
      setRelatedData(initialData);

      const newsId = initialData?.id;
      if (!newsId) {
        setLoadingState("done");
        return;
      }

      setLoadingState("polling");
      setLoadingMessage("Analysis in progress — results appear as they complete…");

      const TIMEOUT_MS = 90_000;
      const startTime  = Date.now();

      const es = new EventSource(`${apiUrl}/application/stream_news?news_id=${newsId}`);
      esRef.current = es;

      es.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          setRelatedData(update);
          if (isAnalysisComplete(update) || Date.now() - startTime > TIMEOUT_MS) {
            es.close();
            esRef.current = null;
            setLoadingState("done");
          }
        } catch (_) { /* ignore parse errors */ }
      };

      es.onerror = () => {
        es.close();
        esRef.current = null;
        setLoadingState("done");
      };

    } catch (err) {
      console.error("[InlineComparison] fetch error:", err);
      setLoadingState("error");
      setLoadingMessage("Could not load analysis for this article.");
    }
  }, [apiUrl]);

  // Re-run whenever a different related article is selected
  useEffect(() => {
    if (!relatedArticle?.url) return;
    setRelatedData(null);
    setLoadingState("idle");
    fetchRelatedAnalysis(relatedArticle.url);

    return () => {
      if (esRef.current) { esRef.current.close(); esRef.current = null; }
    };
  }, [relatedArticle?.url, fetchRelatedAnalysis]);

  if (!analysedArticle || !relatedArticle) return null;

  const isLoading = loadingState === "submitting" || loadingState === "polling";

  const analysedBiasRaw = analysedArticle?.political_bias_result?.rating || "";
  const relatedBiasRaw  = relatedData?.political_bias_result?.rating || relatedArticle?.political_bias || "";

  const aPos = biasPosition(analysedBiasRaw);
  const rPos = biasPosition(relatedBiasRaw);

  const keyDiff = (!isLoading && relatedData && isAnalysisComplete(relatedData))
    ? buildKeyDifference(analysedArticle, relatedData)
    : null;

  const aMarkerStyle = { left: `calc(${(aPos / 4) * 100}% - 12px)`, background: getBias(analysedBiasRaw).color };
  const rMarkerStyle = { left: `calc(${(rPos / 4) * 100}% - 12px)`, background: getBias(relatedBiasRaw).color };
  const aLegendStyle = { background: getBias(analysedBiasRaw).color };
  const rLegendStyle = { background: getBias(relatedBiasRaw).color };

  return (
    <div
      ref={panelRef}
      className="mt-6 rounded-2xl border border-indigo-200 bg-white shadow-lg overflow-hidden"
      style={{ scrollMarginTop: "2rem" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 bg-indigo-50 border-b border-indigo-100">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="p-1.5 bg-indigo-100 rounded-lg">
            <GitCompareArrows className="h-4 w-4 text-indigo-600" />
          </div>
          <h3 className="text-base font-bold text-indigo-900 tracking-tight">Side-by-Side Comparison</h3>
          {isLoading && (
            <span className="flex items-center gap-1.5 text-xs text-indigo-400">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Analysing related article…
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-full hover:bg-indigo-100 transition-colors text-indigo-400 hover:text-indigo-700"
          aria-label="Close comparison"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Key Difference — shown once related analysis is complete */}
      {keyDiff && (
        <div className="px-5 py-3 bg-amber-50 border-b border-amber-100 flex items-start gap-2">
          <span className="text-sm shrink-0 mt-0.5">💡</span>
          <div>
            <span className="text-xs font-bold text-amber-700 uppercase tracking-wider mr-1.5">Key Difference</span>
            <span className="text-xs text-amber-800 leading-relaxed">{keyDiff}</span>
          </div>
        </div>
      )}

      {/* Bias spectrum */}
      <div className="px-5 py-4 border-b border-slate-100">
        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Political Spectrum Positions</p>
        <div className="relative h-6">
          <div className="absolute inset-y-2 inset-x-0 rounded-full bg-gradient-to-r from-blue-200 via-purple-200 to-red-200" />
          <div
            className="absolute top-0 h-6 w-6 rounded-full border-2 border-white shadow-md flex items-center justify-center z-10 transition-all duration-500"
            style={aMarkerStyle}
            title="Analysed article"
          >
            <span className="text-white text-[8px] font-black">A</span>
          </div>
          <div
            className="absolute top-0 h-6 w-6 rounded-full border-2 border-white shadow-md flex items-center justify-center z-10 transition-all duration-500"
            style={rMarkerStyle}
            title="Related article"
          >
            <span className="text-white text-[8px] font-black">R</span>
          </div>
        </div>
        <div className="flex justify-between mt-1.5">
          {["Left", "Leaning L", "Center", "Leaning R", "Right"].map(l => (
            <span key={l} className="text-[9px] text-slate-300 font-medium">{l}</span>
          ))}
        </div>
        <div className="flex gap-3 mt-2">
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded-full border border-white shadow-sm" style={aLegendStyle} />
            <span className="text-[10px] text-slate-500">A = Analysed</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-3 w-3 rounded-full border border-white shadow-sm" style={rLegendStyle} />
            <span className="text-[10px] text-slate-500">R = Related</span>
          </div>
        </div>
      </div>

      {/* Two columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-100">
        <div className="p-5">
          <ArticleColumn
            label="Analysed Article"
            data={analysedArticle}
            isAnalysed={true}
            loading={false}
          />
        </div>
        <div className="p-5">
          <ArticleColumn
            label="Related Article"
            data={relatedData || { url: relatedArticle.url, title: relatedArticle.title, source: relatedArticle.source }}
            isAnalysed={false}
            loading={isLoading}
            loadingMessage={loadingMessage}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
        <p className="text-[11px] text-slate-400 italic">
          {isLoading
            ? "✦ Running full analysis on the related article — results stream in as they complete."
            : "✦ Both articles have been independently analysed through the same pipeline."}
        </p>
        <button
          onClick={onClose}
          className="text-xs font-medium text-slate-500 hover:text-red-500 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-50 border border-transparent hover:border-red-100"
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default InlineComparison;