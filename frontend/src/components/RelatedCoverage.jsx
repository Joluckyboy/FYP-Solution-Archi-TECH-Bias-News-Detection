/**
 * RelatedCoverage.jsx
 *
 * Props:
 *   articleUrl       {string}
 *   analysedArticle  {object}
 *   apiUrl           {string}
 *   hideHeader       {boolean} — hides the section title when used inside a Tab card
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Newspaper, GitCompareArrows,
  ChevronDown, ChevronUp, ExternalLink, Loader2,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

// ─── Bias styling ─────────────────────────────────────────────────────────────

const BIAS_STYLE = {
  left:            { label: "Left",          bg: "bg-blue-100",   text: "text-blue-800",   border: "border-blue-200",   dot: "bg-blue-500"   },
  "leaning-left":  { label: "Leaning Left",  bg: "bg-blue-50",    text: "text-blue-700",   border: "border-blue-100",   dot: "bg-blue-300"   },
  "leaning left":  { label: "Leaning Left",  bg: "bg-blue-50",    text: "text-blue-700",   border: "border-blue-100",   dot: "bg-blue-300"   },
  center:          { label: "Center",        bg: "bg-purple-50",  text: "text-purple-700", border: "border-purple-100", dot: "bg-purple-400" },
  centre:          { label: "Center",        bg: "bg-purple-50",  text: "text-purple-700", border: "border-purple-100", dot: "bg-purple-400" },
  neutral:         { label: "Center",        bg: "bg-purple-50",  text: "text-purple-700", border: "border-purple-100", dot: "bg-purple-400" },
  "leaning-right": { label: "Leaning Right", bg: "bg-red-50",     text: "text-red-700",    border: "border-red-100",    dot: "bg-red-300"    },
  "leaning right": { label: "Leaning Right", bg: "bg-red-50",     text: "text-red-700",    border: "border-red-100",    dot: "bg-red-300"    },
  right:           { label: "Right",         bg: "bg-red-100",    text: "text-red-800",    border: "border-red-200",    dot: "bg-red-500"    },
};

function getBiasStyle(rawBias) {
  const key = (rawBias || "").toLowerCase().trim().replace(/_/g, "-");
  return BIAS_STYLE[key] ?? {
    label: rawBias || "Unknown",
    bg: "bg-slate-100", text: "text-slate-600",
    border: "border-slate-200", dot: "bg-slate-400",
  };
}

function SourceFavicon({ source }) {
  const slug   = (source || "").toLowerCase().replace(/\s+/g, "");
  const domain = `${slug}.com`;
  return (
    <img
      src={`https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${domain}&size=32`}
      alt={source}
      className="h-5 w-5 rounded-full object-contain flex-shrink-0"
      onError={(e) => { e.target.style.display = "none"; }}
    />
  );
}

// ─── Article card ─────────────────────────────────────────────────────────────

function RelatedArticleCard({ article, analysedArticle, apiUrl }) {
  const navigate = useNavigate();
  const bias     = getBiasStyle(article.political_bias);
  const date     = article.published_at ? String(article.published_at).slice(0, 10) : null;
  const [busy, setBusy] = useState(false);

  const handleCompare = async () => {
    if (busy) return;
    setBusy(true);
    try {
      sessionStorage.setItem("comparison_analysed_article", JSON.stringify(analysedArticle));
      sessionStorage.setItem("comparison_related_meta", JSON.stringify({
        url:            article.url,
        title:          article.title,
        source:         article.source,
        political_bias: article.political_bias,
        summary:        article.summary,
      }));
      navigate("/compare");
    } catch (err) {
      console.error("[RelatedCoverage] handleCompare:", err);
      setBusy(false);
    }
  };

  return (
    <div className="group relative rounded-xl border border-slate-200 bg-white transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <div className={`h-1 w-full rounded-t-xl ${bias.dot}`} />
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <SourceFavicon source={article.source} />
            <span className="text-sm font-semibold text-slate-700 truncate">{article.source}</span>
          </div>
          <span className={`flex-shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${bias.bg} ${bias.text} ${bias.border}`}>
            {bias.label}
          </span>
        </div>

        {/* Title */}
        <a
          href={article.url} target="_blank" rel="noopener noreferrer"
          className="block text-sm font-medium text-slate-800 leading-snug mb-2 hover:text-indigo-600 transition-colors line-clamp-3"
        >
          {article.title}
          <ExternalLink className="inline ml-1 h-3 w-3 opacity-40" />
        </a>

        {/* Summary */}
        {article.summary && (
          <p className="text-xs text-slate-500 line-clamp-2 mb-3 leading-relaxed">{article.summary}</p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          {date ? <span className="text-xs text-slate-400">{date}</span> : <span />}
          <button
            onClick={handleCompare}
            disabled={busy}
            className={`
              flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg
              transition-all duration-150 border
              ${busy
                ? "bg-indigo-100 text-indigo-400 border-indigo-200 cursor-not-allowed"
                : "bg-indigo-50 text-indigo-700 hover:bg-indigo-600 hover:text-white border-indigo-200 hover:border-indigo-600"}
            `}
          >
            {busy
              ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Opening…</>
              : <><GitCompareArrows className="h-3.5 w-3.5" /> Compare</>}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function RelatedCoverageSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[1, 2, 3].map(i => (
        <div key={i} className="rounded-xl border border-slate-100 bg-white overflow-hidden">
          <div className="h-1 w-full bg-slate-100" />
          <div className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-5 rounded-full" />
              <Skeleton className="h-4 w-28" />
            </div>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-3 w-full" />
            <div className="pt-2 flex justify-between items-center">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-7 w-24 rounded-lg" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

const RelatedCoverage = ({ articleUrl, analysedArticle, apiUrl, hideHeader = false }) => {
  const [articles,     setArticles]     = useState([]);
  const [clusterTitle, setClusterTitle] = useState("");
  const [loading,      setLoading]      = useState(false);
  const [matched,      setMatched]      = useState(false);
  const [reason,       setReason]       = useState("");
  const [showAll,      setShowAll]      = useState(false);

  const INITIAL_SHOW = 6;

  useEffect(() => {
    if (!articleUrl || !apiUrl) return;
    let cancelled = false;
    setLoading(true);

    fetch(`${apiUrl}/application/related_coverage?url=${encodeURIComponent(articleUrl)}`)
      .then(r => r.json())
      .then(data => {
        if (cancelled) return;
        // Backend already handles:
        // - 1 article per outlet (seen_sources in filter_related)
        // - Exclude submitter's outlet (slug + display name mapping)
        // - Sort by political bias left → right
        // - Most recent article per outlet
        setArticles(data.articles || []);
        setClusterTitle(data.cluster_title || "");
        setMatched(data.matched ?? false);
        setReason(data.reason || "");
      })
      .catch(() => {
        if (!cancelled) { setMatched(false); setReason("Related coverage unavailable"); }
      })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [articleUrl, apiUrl]);

  const visibleArticles = showAll ? articles : articles.slice(0, INITIAL_SHOW);
  const hiddenCount     = articles.length - INITIAL_SHOW;

  return (
    <div>
      {/* Section header — hidden when used inside a Tab (hideHeader=true) */}
      {!hideHeader && (
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 bg-indigo-50 rounded-lg">
            <Newspaper className="h-5 w-5 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-800 leading-tight">Related Coverage</h2>
            {!loading && matched && (
              <p className="text-xs text-slate-400 mt-0.5">
                Same story, different outlets — click <strong>Compare</strong> for a side-by-side analysis
              </p>
            )}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && <RelatedCoverageSkeleton />}

      {/* No match */}
      {!loading && !matched && (
        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-6 py-10 text-center">
          <Newspaper className="h-8 w-8 text-slate-300 mx-auto mb-2" />
          <p className="text-sm font-medium text-slate-500">No related coverage found</p>
          <p className="text-xs text-slate-400 mt-1">
            {reason || "This article doesn't closely match any story in our database."}
          </p>
        </div>
      )}

      {/* Matched articles */}
      {!loading && matched && articles.length > 0 && (
        <>
          {clusterTitle && (
            <div className="mb-4 px-4 py-2.5 bg-indigo-50 border border-indigo-100 rounded-lg inline-flex items-center gap-2">
              <span className="text-xs text-indigo-500 font-semibold uppercase tracking-wider">Matched story</span>
              <span className="text-sm text-indigo-800 font-medium">{clusterTitle}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {visibleArticles.map((article, idx) => (
              <RelatedArticleCard
                key={`${article.source}-${idx}`}
                article={article}
                analysedArticle={analysedArticle}
                apiUrl={apiUrl}
              />
            ))}
          </div>

          {hiddenCount > 0 && (
            <div className="mt-4 flex justify-center">
              <button
                onClick={() => setShowAll(v => !v)}
                className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-indigo-600 transition-colors px-4 py-2 rounded-full border border-slate-200 bg-white hover:border-indigo-200"
              >
                {showAll
                  ? <><ChevronUp className="h-4 w-4" /> Show less</>
                  : <><ChevronDown className="h-4 w-4" /> Show {hiddenCount} more article{hiddenCount !== 1 ? "s" : ""}</>}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RelatedCoverage;