import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import get_api from "@/config/config";
import ReactMarkdown from "react-markdown";
import {
  ArrowLeft, GitCompareArrows, ExternalLink,
  TrendingUp, TrendingDown, Minus, Loader2, RefreshCw, FileText,
} from "lucide-react";
import { HashLoader } from "react-spinners";
import "../index.css";
import { normalizeBias } from "@/utils/biasNormalizer";

// ─── Side colours ─────────────────────────────────────────────────────────────

const L_COLOR  = "#166534";
const L_LIGHT  = "#f0fdf4";
const L_BORDER = "#16a34a";
const R_COLOR  = "#5b21b6";
const R_LIGHT  = "#faf5ff";
const R_BORDER = "#7c3aed";

// ─── Bias ─────────────────────────────────────────────────────────────────────

const BIAS_STYLE = {
  left:         { label: "Left",       color: "#1d4ed8", bg: "#dbeafe", border: "#93c5fd" },
  "lean-left":  { label: "Lean Left",  color: "#2563eb", bg: "#eff6ff", border: "#bfdbfe" },
  center:       { label: "Center",     color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe" },
  "lean-right": { label: "Lean Right", color: "#dc2626", bg: "#fff1f2", border: "#fecaca" },
  right:        { label: "Right",      color: "#b91c1c", bg: "#fee2e2", border: "#fca5a5" },
};
const BIAS_SPECTRUM = ["left", "lean-left", "center", "lean-right", "right"];

function getBias(raw) {
  const key = normalizeBias(raw);
  return BIAS_STYLE[key] ?? { label: raw || "—", color: "#64748b", bg: "#f8fafc", border: "#e2e8f0" };
}
function biasPos(raw) {
  const idx = BIAS_SPECTRUM.indexOf(normalizeBias(raw));
  return idx === -1 ? 2 : idx;
}

// ─── Analysis helpers ─────────────────────────────────────────────────────────

function dominantSentiment(r) {
  if (!r || !Object.keys(r).length) return null;
  const { positive=0, negative=0, neutral=0 } = r;
  if (positive>=negative && positive>=neutral) return { label:"Positive", value:positive, color:"#16a34a", Icon:TrendingUp };
  if (negative>=positive && negative>=neutral) return { label:"Negative", value:negative, color:"#dc2626", Icon:TrendingDown };
  return { label:"Neutral", value:neutral, color:"#64748b", Icon:Minus };
}
function dominantEmotion(r) {
  if (!r?.dominant_emotion) return null;
  const em = r.dominant_emotion;
  return `${em.charAt(0).toUpperCase()+em.slice(1)} (${((r.dominant_score??0) * 100).toFixed(1)}%)`;
}
function propagandaScore(r) {
  return r?.propaganda_probability != null ? parseFloat((r.propaganda_probability * 100).toFixed(1)) : null;
}
function factcheckSummary(r) {
  if (!Array.isArray(r)||!r.length) return null;
  const total = r.length;
  const factual   = r.filter(f=>(f.correctness||"").toLowerCase()==="factual").length;
  const unfactual = r.filter(f=>(f.correctness||"").toLowerCase()==="unfactual").length;
  return { total, factual, unfactual, unclear: total-factual-unfactual };
}
function isComplete(d) {
  return !!(
    d?.sentiment_result   && Object.keys(d.sentiment_result).length &&
    d?.emotion_result     && Object.keys(d.emotion_result).length &&
    d?.propaganda_result  && d.propaganda_result.propaganda_probability != null &&
    Array.isArray(d?.factcheck_result) && d.factcheck_result.length > 0 &&
    d?.political_bias_result?.rating
  );
}

// ─── Key Difference ───────────────────────────────────────────────────────────

function KeyDifference({ left, right }) {
  if (!left||!right||!isComplete(left)||!isComplete(right)) return null;
  const diffs = [];
  const lB = left?.political_bias_result?.rating||"";
  const rB = right?.political_bias_result?.rating||"";
  const gap = Math.abs(biasPos(lB)-biasPos(rB));
  if (gap>=2) diffs.push(`Opposite ends of the spectrum — ${getBias(lB).label} vs ${getBias(rB).label}.`);
  else if (gap===1) diffs.push(`Slightly different political leanings — ${getBias(lB).label} vs ${getBias(rB).label}.`);
  const lS = dominantSentiment(left?.sentiment_result);
  const rS = dominantSentiment(right?.sentiment_result);
  if (lS&&rS&&lS.label!==rS.label) diffs.push(`Tone: ${lS.label.toLowerCase()} vs ${rS.label.toLowerCase()}.`);
  const lP = propagandaScore(left?.propaganda_result);
  const rP = propagandaScore(right?.propaganda_result);
  if (lP!=null&&rP!=null&&Math.abs(lP-rP)>=20)
    diffs.push(`${lP>rP?"This":"The related"} article uses notably more influence language (${Math.max(lP,rP)}% vs ${Math.min(lP,rP)}%).`);
  const text = diffs.length===0
    ? "Both articles cover the same story with similar framing."
    : diffs.join(" ");
  return (
    <div className="flex items-start gap-3 px-5 py-4 bg-amber-50 border border-amber-200 rounded-xl mb-6">
      <span className="text-xl shrink-0">💡</span>
      <div>
        <p className="text-md font-bold text-amber-700 uppercase tracking-wider mb-1">Key Difference</p>
        <p className="text-md text-amber-900 leading-relaxed">{text}</p>
      </div>
    </div>
  );
}

// ─── Pending ──────────────────────────────────────────────────────────────────

function Pending({ loading }) {
  return (
    <div className="flex items-center gap-2 text-slate-400">
      {loading
        ? <><Loader2 className="h-4 w-4 animate-spin text-violet-400" /><span className="text-sm italic">Analysing…</span></>
        : <span className="text-sm italic">Not available</span>}
    </div>
  );
}

// ─── Cell components — same visual style as ResultsPage ──────────────────────

function BiasCell({ data, loading }) {
  const raw  = data?.political_bias_result?.rating || "";
  const bias = getBias(raw);
  if (!raw) return <Pending loading={loading} />;
  return (
    <div className="rounded-xl px-4 py-3" style={{ background: bias.bg, border: `1px solid ${bias.border}` }}>
      <p className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color: bias.color, opacity: 0.7 }}>
        Political Bias
      </p>
      <p className="text-lg font-bold" style={{ color: bias.color }}>{bias.label}</p>
    </div>
  );
}

function TopicsCell({ data, loading }) {
  const topics = data?.political_bias_result?.topics;
  if (!topics) return <Pending loading={loading} />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {/* Covered */}
      <div className="rounded-xl border border-green-100 bg-green-50 px-3 py-2.5">
        <p className="text-xs font-bold uppercase tracking-wider text-green-700 mb-2">Topics Covered</p>
        <ul className="space-y-1.5">
          {(topics.covered||[]).slice(0,4).map((t,i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-green-800">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-500 shrink-0" />{t}
            </li>
          ))}
        </ul>
      </div>
      {/* Omitted */}
      <div className="rounded-xl border border-rose-100 bg-rose-50 px-3 py-2.5">
        <p className="text-xs font-bold uppercase tracking-wider text-rose-700 mb-2">Topics Omitted</p>
        <ul className="space-y-1.5">
          {(topics.omitted||[]).slice(0,4).map((t,i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-rose-800">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-rose-500 shrink-0" />{t}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

const SENTIMENT_EMOJI = { Positive: "😊", Negative: "😟", Neutral: "😐" };

function SentimentCell({ data, loading }) {
  const sent = dominantSentiment(data?.sentiment_result);
  if (!sent) return <Pending loading={loading} />;
  const emoji = SENTIMENT_EMOJI[sent.label] ?? "😐";
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-3xl">{emoji}</span>
        <span className="text-base font-bold" style={{ color: sent.color }}>
          {sent.label}
          <span className="text-sm font-normal text-slate-400 ml-1.5">({(sent.value*100).toFixed(1)}%)</span>
        </span>
      </div>
      <div className="space-y-2">
        {[{key:"positive",color:"#22c55e"},{key:"negative",color:"#ef4444"},{key:"neutral",color:"#94a3b8"}]
          .map(({key,color}) => {
            const val = parseFloat(((data.sentiment_result[key] ?? 0) * 100).toFixed(1));
            return (
              <div key={key} className="flex items-center gap-3">
                <span className="text-sm text-slate-500 w-16 capitalize">{key}</span>
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width:`${val}%`, background:color }} />
                </div>
                <span className="text-sm text-slate-600 w-10 text-right">{val}%</span>
              </div>
            );
          })}
      </div>
    </div>
  );
}

const EMOTION_EMOJI_MAP = {
  joy:"😄", love:"❤️", excitement:"🎉", fear:"😨", anger:"😡",
  sadness:"😢", neutral:"😐", optimism:"🌟", curiosity:"🤔",
  approval:"👍", disapproval:"👎", disappointment:"😞", annoyance:"😤",
  confusion:"😕", admiration:"🤩", surprise:"😮", caring:"🤗",
  relief:"😌", realization:"💡", pride:"🦁", grief:"😭",
  remorse:"😔", embarrassment:"😳", nervousness:"😰",
};

function EmotionCell({ data, loading }) {
  const e = dominantEmotion(data?.emotion_result);
  if (!e) return <Pending loading={loading} />;
  const emotionKey = (data?.emotion_result?.dominant_emotion || "").toLowerCase();
  const emoji = EMOTION_EMOJI_MAP[emotionKey] ?? "🎭";
  return (
    <div className="flex items-center gap-2">
      <span className="text-3xl">{emoji}</span>
      <p className="text-lg font-bold text-slate-700">{e}</p>
    </div>
  );
}

function PropCell({ data, loading }) {
  const prop = propagandaScore(data?.propaganda_result);
  if (prop==null) return <Pending loading={loading} />;
  const barCls   = prop>=65 ? "bg-red-400"   : prop>=35 ? "bg-amber-400" : "bg-green-400";
  const badgeCls = prop>=65 ? "bg-red-100 text-red-700" : prop>=35 ? "bg-amber-100 text-amber-700" : "bg-green-100 text-green-700";
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl font-bold text-slate-700">{prop.toFixed(1)}%</span>
        <span className={`text-sm font-bold px-3 py-1 rounded-full ${badgeCls}`}>
          {prop>=65 ? "High" : prop>=35 ? "Moderate" : "Low"}
        </span>
      </div>
      <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${barCls}`} style={{ width:`${prop}%` }} />
      </div>
    </div>
  );
}

function FactCell({ data, loading }) {
  const facts = factcheckSummary(data?.factcheck_result);
  if (!facts) return <Pending loading={loading} />;
  return (
    <div className="flex flex-wrap gap-2">
      <span className="text-sm bg-teal-100 text-teal-700 px-3 py-1 rounded-full font-semibold">✅ {facts.factual} verified</span>
      <span className="text-sm bg-amber-100 text-amber-700 px-3 py-1 rounded-full font-semibold">🔍 {facts.unclear} unclear</span>
      {facts.unfactual>0 && <span className="text-sm bg-rose-100 text-rose-700 px-3 py-1 rounded-full font-semibold">❌ {facts.unfactual} false</span>}
      <span className="text-sm bg-slate-100 text-slate-500 px-3 py-1 rounded-full font-semibold">{facts.total} total</span>
    </div>
  );
}

function SummaryContent({ text }) {
  const hasMarkdownList = /^[\s]*[-*\d]/m.test(text);

  if (hasMarkdownList) {
    return (
      <ReactMarkdown
        components={{
          ul: ({ children }) => <ul className="space-y-2">{children}</ul>,
          ol: ({ children }) => <ol className="space-y-2">{children}</ol>,
          li: ({ children }) => (
            <li className="flex items-start gap-2 text-sm text-slate-600">
              <span className="shrink-0 mt-1.5 h-1.5 w-1.5 rounded-full bg-slate-400" />
              <span className="leading-relaxed">{children}</span>
            </li>
          ),
          p: ({ children }) => <p className="text-sm text-slate-600 leading-relaxed mb-1.5">{children}</p>,
          strong: ({ children }) => <span className="font-semibold text-slate-800">{children}</span>,
        }}
      >
        {text}
      </ReactMarkdown>
    );
  }

  // Split into individual sentences regardless of newlines
  const sentences = text
    .replace(/\n+/g, " ")             // flatten all newlines to space
    .split(/(?<=[.!?])\s+/)           // split after every sentence-ending punctuation
    .map(s => s.trim())
    .filter(s => s.length > 20);      // drop tiny fragments

  return (
    <ul className="space-y-2">
      {sentences.map((s, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
          <span className="shrink-0 mt-1.5 h-1.5 w-1.5 rounded-full bg-slate-400" />
          <span className="leading-relaxed">{s}</span>
        </li>
      ))}
    </ul>
  );
}

function SummaryCell({ data, loading }) {
  if (!data?.summarise_result) return <Pending loading={loading} />;
  return (
    <div className="max-h-64 overflow-y-auto pr-1">
      <SummaryContent text={data.summarise_result} dotColor="bg-slate-400" />
    </div>
  );
}

// ─── Row definition ───────────────────────────────────────────────────────────

const ROWS = [
  { label: "Political Bias",            Cell: BiasCell      },
  { label: "Topics Covered & Omitted",  Cell: TopicsCell    },
  { label: "Sentiment Tone",            Cell: SentimentCell },
  { label: "Dominant Emotion",          Cell: EmotionCell   },
  { label: "Propaganda Score",          Cell: PropCell      },
  { label: "Fact-Check Summary",        Cell: FactCell      },
  { label: "Article Summary",           Cell: SummaryCell   },
];

// ─── Unified comparison table ─────────────────────────────────────────────────

function ComparisonTable({ left, right, isLoading, lDomain, rDomain, lNewsId, rNewsId, relatedMeta, onViewLeft, onViewRight }) {
  return (
    <div className="rounded-2xl overflow-hidden bg-white shadow-sm"
      style={{ border: "1px solid #e2e8f0" }}>

      {/* ── Column headers ─────────────────────────────────────────────── */}
      {/* Mobile: stacked. md+: side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2">

        {/* Left header */}
        <div className="px-5 py-5 border-b md:border-b-0 md:border-r border-slate-200"
          style={{ borderLeft: `4px solid ${L_BORDER}`, borderTop: `4px solid ${L_BORDER}` }}>
          <div className="inline-block text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full mb-3"
            style={{ background: L_LIGHT, color: L_COLOR, border: `1px solid #bbf7d0` }}>
            This Article
          </div>
          <div className="flex items-center gap-2 mb-1">
            <img
              src={`https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${lDomain}&size=32`}
              alt="" className="h-5 w-5 rounded-full shrink-0"
              onError={(e)=>{e.target.style.display="none";}} />
            <span className="text-sm text-slate-400 font-medium">{left?.source||lDomain}</span>
          </div>
          <p className="text-md font-bold text-slate-800 leading-snug mb-3">{left?.title}</p>
          <div className="flex flex-wrap items-center gap-2">
            <a href={left?.url} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors px-3 py-1.5 rounded-lg border border-slate-200 hover:border-slate-300 bg-slate-50">
              <ExternalLink className="h-3.5 w-3.5" /> Open article
            </a>
            {lNewsId && (
              <button onClick={onViewLeft}
                className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
                style={{ background: L_LIGHT, color: L_COLOR, border: `1px solid #bbf7d0` }}>
                <FileText className="h-3.5 w-3.5" /> Full analysis
              </button>
            )}
          </div>
        </div>

        {/* Right header */}
        <div className="px-5 py-5"
          style={{ borderRight: `4px solid ${R_BORDER}`, borderTop: `4px solid ${R_BORDER}` }}>
          <div className="inline-block text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full mb-3"
            style={{ background: R_LIGHT, color: R_COLOR, border: `1px solid #ddd6fe` }}>
            Related Article
          </div>
          <div className="flex items-center gap-2 mb-1">
            <img
              src={`https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${rDomain}&size=32`}
              alt="" className="h-5 w-5 rounded-full shrink-0"
              onError={(e)=>{e.target.style.display="none";}} />
            <span className="text-sm text-slate-400 font-medium">{relatedMeta?.source||rDomain}</span>
          </div>
          <p className="text-md font-bold text-slate-800 leading-snug mb-3">{relatedMeta?.title}</p>
          <div className="flex flex-wrap items-center gap-2">
            <a href={relatedMeta?.url} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors px-3 py-1.5 rounded-lg border border-slate-200 hover:border-slate-300 bg-slate-50">
              <ExternalLink className="h-3.5 w-3.5" /> Open article
            </a>
            {rNewsId && (
              <button onClick={onViewRight}
                className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
                style={{ background: R_LIGHT, color: R_COLOR, border: `1px solid #ddd6fe` }}>
                <FileText className="h-3.5 w-3.5" /> Full analysis
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Metric rows ─────────────────────────────────────────────────── */}
      {/* Mobile: each row stacks left cell on top of right cell.
          md+:    side by side in two columns.
          On mobile the left cell gets a green top border,
          the right cell gets a violet top border so the user
          still knows which article they're reading. */}
      {ROWS.map(({ label, Cell }, idx) => {
        const isLast = idx === ROWS.length - 1;
        return (
          <div key={label}
            className={`grid grid-cols-1 md:grid-cols-2 border-t border-slate-100 ${idx%2===0 ? "bg-white" : "bg-slate-50/50"}`}>

            {/* Left cell */}
            <div className="px-5 py-5 border-b md:border-b-0 md:border-r border-slate-200"
              style={{
                borderLeft:   `4px solid ${L_BORDER}`,
                ...(isLast ? { borderBottom: `4px solid ${L_BORDER}` } : {}),
              }}>
              {/* Mobile-only: show "This Article" label above the metric */}
              <p className="text-xs font-bold uppercase tracking-widest mb-1 md:hidden"
                style={{ color: L_COLOR }}>This Article</p>
              <p className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">{label}</p>
              <Cell data={left} loading={false} />
            </div>

            {/* Right cell */}
            <div className="px-5 py-5"
              style={{
                borderRight: `4px solid ${R_BORDER}`,
                ...(isLast ? { borderBottom: `4px solid ${R_BORDER}` } : {}),
              }}>
              {/* Mobile-only: show "Related Article" label above the metric */}
              <p className="text-xs font-bold uppercase tracking-widest mb-1 md:hidden"
                style={{ color: R_COLOR }}>Related Article</p>
              <p className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">{label}</p>
              <Cell data={right} loading={isLoading} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

const ComparisonPage = () => {
  const navigate = useNavigate();

  const [analysedArticle, setAnalysedArticle] = useState(null);
  const [relatedMeta,     setRelatedMeta]     = useState(null);
  const [API_URL,         setAPI_URL]         = useState(null);
  const [relatedData,     setRelatedData]     = useState(null);
  const [relatedNewsId,   setRelatedNewsId]   = useState(null);
  const [loadingStage,    setLoadingStage]    = useState("idle");
  const esRef = useRef(null);

  useEffect(() => {
    try {
      const a = sessionStorage.getItem("comparison_analysed_article");
      const r = sessionStorage.getItem("comparison_related_meta");
      if (a) setAnalysedArticle(JSON.parse(a));
      if (r) setRelatedMeta(JSON.parse(r));
    } catch (e) { console.error("[ComparisonPage]", e); }
    get_api().then(setAPI_URL);
  }, []);

  const fetchRelatedAnalysis = useCallback(async (articleUrl) => {
    if (!API_URL||!articleUrl) return;
    if (esRef.current) { esRef.current.close(); esRef.current=null; }
    try {
      setLoadingStage("submitting");
      const resp = await fetch(`${API_URL}/application/new_query`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ url:articleUrl, background:true, force:false }),
      });
      if (!resp.ok) throw new Error(`${resp.status}`);
      const initial = await resp.json();
      setRelatedData(initial);
      const newsId = initial?.id;
      if (newsId) setRelatedNewsId(newsId);
      if (isComplete(initial)) { setLoadingStage("done"); return; }
      if (!newsId)              { setLoadingStage("done"); return; }
      setLoadingStage("polling");
      const t0 = Date.now();
      const es = new EventSource(`${API_URL}/application/stream_news?news_id=${newsId}`);
      esRef.current = es;
      es.onmessage = (ev) => {
        try {
          const u = JSON.parse(ev.data);
          setRelatedData(u);
          if (isComplete(u)||Date.now()-t0>90_000) {
            es.close(); esRef.current=null; setLoadingStage("done");
          }
        } catch (e) { console.error("[ComparisonPage] SSE parse error:", e); }
      };
      es.onerror = () => { es.close(); esRef.current=null; setLoadingStage("done"); };
    } catch(err) {
      console.error("[ComparisonPage]", err);
      setLoadingStage("error");
    }
  }, [API_URL]);

  useEffect(() => {
    if (API_URL&&relatedMeta?.url) fetchRelatedAnalysis(relatedMeta.url);
    return () => { if(esRef.current){esRef.current.close();esRef.current=null;} };
  }, [API_URL, relatedMeta?.url, fetchRelatedAnalysis]);

  if (!analysedArticle||!relatedMeta) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center space-y-3">
          <p className="text-slate-500 text-sm">No comparison data found.</p>
          <p className="text-slate-400 text-xs">Navigate here from a Related Coverage card.</p>
          <button onClick={()=>navigate(-1)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const isLoading = loadingStage==="submitting"||loadingStage==="polling";
  const left      = analysedArticle;
  const right     = relatedData;

  const lDomain = (()=>{ try{return new URL(left?.url||"").hostname.replace("www.","");} catch{return left?.source||"";} })();
  const rDomain = (()=>{ try{return new URL(relatedMeta?.url||"").hostname.replace("www.","");} catch{return relatedMeta?.source||"";} })();

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Sticky subnav — plain full-width div, NOT inside app-container,
          so it aligns flush with the app navbar above */}
      <div className="sticky top-20 z-20 bg-white border-b border-slate-200 shadow-sm">
        <div className="w-full px-4 py-2.5 flex items-center justify-between gap-2">
          <button onClick={()=>navigate(-1)}
            className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 px-2 sm:px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors shrink-0">
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Back</span>
          </button>
          <div className="flex items-center gap-1.5 min-w-0">
            <GitCompareArrows className="h-4 w-4 text-indigo-500 shrink-0" />
            <span className="text-md font-bold text-slate-700 truncate">Article Comparison</span>
            {isLoading && (
              <span className="flex items-center gap-1 text-xs text-indigo-400 shrink-0">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span className="hidden sm:inline">Analysing…</span>
              </span>
            )}
            {loadingStage==="done" && (
              /* Always show on mobile too — but keep it compact */
              <span className="text-sm text-green-600 font-semibold shrink-0">
                ✓ <span className="hidden sm:inline">Both ready</span>
              </span>
            )}
          </div>
          <button
            onClick={()=>{ setRelatedData(null); setLoadingStage("idle"); fetchRelatedAnalysis(relatedMeta.url); }}
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-indigo-600 px-2 sm:px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors shrink-0">
            <RefreshCw className="h-4 w-4" />
            <span className="hidden sm:inline">Retry</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-3 sm:px-4 py-4 sm:py-6">

        <KeyDifference left={left} right={right} />

        {/* Loading banner while waiting for first response */}
        {isLoading && !right && (
          <div className="bg-white rounded-2xl border border-violet-100 px-6 py-10 text-center space-y-4 mb-6">
            <HashLoader color="#7c3aed" size={40} cssOverride={{ margin:"0 auto" }} />
            <p className="text-base font-medium text-slate-600">
              {loadingStage==="submitting" ? "Submitting related article for analysis…" : "Running all 5 analysis services in parallel…"}
            </p>
            <p className="text-sm text-slate-400">Sentiment · Emotion · Propaganda · Fact-check · Political bias</p>
            <p className="text-sm text-slate-300">Results stream in as each service completes</p>
          </div>
        )}

        <ComparisonTable
          left={left}
          right={right}
          isLoading={isLoading}
          lDomain={lDomain}
          rDomain={rDomain}
          lNewsId={left?.id}
          rNewsId={relatedNewsId}
          relatedMeta={relatedMeta}
          onViewLeft={()=>navigate(`/results/${left.id}`, { state:{ data:left } })}
          onViewRight={()=>relatedNewsId && navigate(`/results/${relatedNewsId}`, { state:{ data:right } })}
        />

        <p className="text-center text-sm text-slate-400 mt-6 pb-6">
          ✦ Click <strong>Full analysis</strong> above to open the complete detailed breakdown for either article.
        </p>
      </div>
    </div>
  );
};

export default ComparisonPage;