import { useEffect, useState, useMemo } from "react";

// ─── Trust score calculation ──────────────────────────────────────────────────
// 50 pts: Fact Accuracy   (factual=1.0, cannot_be_determined=0.5, unfactual=0.0)
// 50 pts: Low Influence   (1 − propaganda_probability) × 50
// Source credibility: NO longer subtracted — shown as a warning banner instead

function computeTrustScore({ factcheckResult, propagandaResult }) {
  const factReady =
    Array.isArray(factcheckResult) && factcheckResult.length > 0;
  const propReady =
    propagandaResult?.propaganda_probability !== undefined &&
    propagandaResult?.propaganda_probability !== null;

  if (!factReady && !propReady) {
    return { ready: false, status: "loading", loadingServices: ["fact-check", "propaganda"] };
  }
  if (!factReady) {
    return { ready: false, status: "loading", loadingServices: ["fact-check"] };
  }
  if (!propReady) {
    return { ready: false, status: "loading", loadingServices: ["propaganda"] };
  }

  // Fact accuracy — weighted
  const total = factcheckResult.length;
  const weightedSum = factcheckResult.reduce((acc, f) => {
    const c = (f.correctness ?? "").toLowerCase();
    if (c === "factual")                return acc + 1.0;
    if (c === "cannot be determined")   return acc + 0.5;
    return acc; // unfactual = 0
  }, 0);
  const factScore = total > 0 ? Math.round((weightedSum / total) * 50) : 0;

  // Propaganda score
  const propProb  = propagandaResult.propaganda_probability ?? 0;
  const propScore = Math.round((1 - propProb) * 50);

  const total100 = Math.min(100, Math.max(0, factScore + propScore));

  return {
    ready:      true,
    total:      total100,
    factScore,
    propScore,
    factTotal:  total,
    factCounts: {
      factual:   factcheckResult.filter(f => (f.correctness ?? "").toLowerCase() === "factual").length,
      unclear:   factcheckResult.filter(f => (f.correctness ?? "").toLowerCase() === "cannot be determined").length,
      unfactual: factcheckResult.filter(f => (f.correctness ?? "").toLowerCase() === "unfactual").length,
    },
  };
}

// ─── Verdict config ───────────────────────────────────────────────────────────
const VERDICT = {
  "Trustworthy": {
    label: "Trustworthy", emoji: "✅",
    color: "#065f46", bg: "#d1fae5", ring: "#6ee7b7", bar: "#10b981",
    explanation: "This article appears factually sound with low influence language.",
  },
  "Read with Caution": {
    label: "Read with Caution", emoji: "⚠️",
    color: "#92400e", bg: "#fef3c7", ring: "#fcd34d", bar: "#f59e0b",
    explanation: "Some claims may need independent verification. Watch for persuasive language.",
  },
  "Treat with Scepticism": {
    label: "Treat with Scepticism", emoji: "🔶",
    color: "#9a3412", bg: "#fff7ed", ring: "#fdba74", bar: "#f97316",
    explanation: "Notable signs of factual issues or influence techniques detected.",
  },
  "Likely Misleading": {
    label: "Likely Misleading", emoji: "🚨",
    color: "#991b1b", bg: "#fee2e2", ring: "#fca5a5", bar: "#ef4444",
    explanation: "Strong indicators of misinformation or propaganda. Verify independently.",
  },
};

function getVerdict(score) {
  if (score >= 70) return VERDICT["Trustworthy"];
  if (score >= 50) return VERDICT["Read with Caution"];
  if (score >= 30) return VERDICT["Treat with Scepticism"];
  return VERDICT["Likely Misleading"];
}

// ─── Source credibility styles ────────────────────────────────────────────────
const CREDIBILITY_STYLE = {
  "Highly Credible":     { color: "#065f46", bg: "#d1fae5", dot: "#10b981", border: "#6ee7b7" },
  "Moderately Credible": { color: "#1e40af", bg: "#dbeafe", dot: "#3b82f6", border: "#93c5fd" },
  "Questionable":        { color: "#92400e", bg: "#fef3c7", dot: "#f59e0b", border: "#fcd34d" },
  "Low Credibility":     { color: "#991b1b", bg: "#fee2e2", dot: "#ef4444", border: "#fca5a5" },
  "Insufficient Data":   { color: "#4b5563", bg: "#f3f4f6", dot: "#9ca3af", border: "#d1d5db" },
};

// ─── Source warning banner — replaces the old ±modifier math ─────────────────
function SourceWarningBanner({ credibility }) {
  if (!credibility || credibility.status !== "ok") return null;
  const label = credibility.label;
  if (label !== "Low Credibility" && label !== "Questionable") return null;

  const isLow = label === "Low Credibility";

  return (
    <div
      className="rounded-lg px-3 py-2.5 flex gap-2 items-start"
      style={{
        background: isLow ? "#fee2e2" : "#fef3c7",
        border:     `0.5px solid ${isLow ? "#fca5a5" : "#fcd34d"}`,
        marginTop:  "0.75rem",
      }}
    >
      <span className="text-base shrink-0">{isLow ? "🚩" : "⚠️"}</span>
      <div>
        <p className="text-xs font-semibold" style={{ color: isLow ? "#991b1b" : "#92400e" }}>
          {isLow ? "Low credibility source" : "Questionable source"}
        </p>
        <p className="text-xs leading-relaxed mt-0.5" style={{ color: isLow ? "#7f1d1d" : "#78350f" }}>
          {isLow
            ? "Past articles from this outlet showed consistently low fact accuracy and heavy use of influence techniques. Cross-check key claims before drawing conclusions."
            : "This outlet has a below-average credibility record. Past articles showed mixed fact accuracy. Apply extra scrutiny to claims in this article."}
        </p>
        <p className="text-xs mt-1 italic" style={{ color: isLow ? "#991b1b" : "#92400e", opacity: 0.75 }}>
          This does not affect the score above — the score reflects only this article's content.
        </p>
      </div>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
const BIAS_DISPLAY = {
  "left":          { label: "Left",          color: "#1e40af" },
  "leaning-left":  { label: "Leaning Left",  color: "#2563eb" },
  "center":        { label: "Center",        color: "#374151" },
  "leaning-right": { label: "Leaning Right", color: "#b91c1c" },
  "right":         { label: "Right",         color: "#991b1b" },
};

function domainFromUrl(url) {
  try { return new URL(url).hostname.replace("www.", ""); }
  catch { return url ?? ""; }
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function MetricCard({ label, value, valueColor }) {
  return (
    <div className="bg-gray-50 rounded-lg p-2.5">
      <p className="text-xs text-gray-400 mb-0.5 leading-snug">{label}</p>
      <p className="text-sm font-semibold leading-snug" style={{ color: valueColor || undefined }}>
        {value}
      </p>
    </div>
  );
}

function ScoreRow({ label, score, max, icon }) {
  const pct      = Math.round((score / max) * 100);
  const barColor = pct >= 65 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs text-gray-500">{icon} {label}</span>
        <span className="text-xs font-medium text-gray-700">{score}/{max}</span>
      </div>
      <div className="w-full h-1.5 bg-gray-100 rounded-full">
        <div
          className="h-1.5 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
    </div>
  );
}

function ProfileRow({ dotColor, label, value, valueColor }) {
  return (
    <div className="flex items-center gap-2.5 bg-gray-50 rounded-lg px-2.5 py-2">
      <span
        className="rounded-full shrink-0"
        style={{ width: 8, height: 8, background: dotColor || "#9ca3af", display: "inline-block" }}
      />
      <div>
        <p className="text-xs text-gray-400 leading-none mb-0.5">{label}</p>
        <p className="text-sm font-medium leading-none" style={{ color: valueColor || undefined }}>{value}</p>
      </div>
    </div>
  );
}

function ProfileRowLoading({ label, reason }) {
  return (
    <div className="flex items-center gap-2.5 bg-gray-50 rounded-lg px-2.5 py-2">
      <span
        className="rounded-full shrink-0 animate-pulse"
        style={{ width: 8, height: 8, background: "#e5e7eb", display: "inline-block" }}
      />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-400 leading-none mb-1">{label}</p>
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-24 bg-gray-200 rounded animate-pulse" />
          <span className="text-xs text-gray-300 truncate">{reason}</span>
        </div>
      </div>
    </div>
  );
}

// Fact count pills shown inside the breakdown
function FactPills({ counts, total }) {
  if (!counts || !total) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-1">
      <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-100">
        ✅ {counts.factual} verified
      </span>
      <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-100">
        🔍 {counts.unclear} unclear <span className="opacity-60">(half weight)</span>
      </span>
      {counts.unfactual > 0 && (
        <span className="text-xs px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-100">
          ❌ {counts.unfactual} unverified
        </span>
      )}
      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-50 text-gray-500 border border-gray-100">
        {total} total claims
      </span>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
const TrustSnapshot = ({ data, apiUrl }) => {
  const [credibility, setCredibility] = useState(null);
  const [credLoading, setCredLoading] = useState(false);
  const [showCalc,    setShowCalc]    = useState(false);

  useEffect(() => {
    if (!apiUrl || !data?.url) return;
    const domain = domainFromUrl(data.url);
    setCredLoading(true);
    fetch(`${apiUrl}/application/source_credibility?domain=${encodeURIComponent(domain)}`)
      .then(r => r.json())
      .then(setCredibility)
      .catch(() => setCredibility(null))
      .finally(() => setCredLoading(false));
  }, [apiUrl, data?.url]);

  // Clean 50/50 score — no source modifier baked in
  const trust = useMemo(() => {
    if (!data) return null;
    return computeTrustScore({
      factcheckResult:  data.factcheck_result,
      propagandaResult: data.propaganda_result,
    });
  }, [data, data?.factcheck_result, data?.propaganda_result]);

  if (!data) return null;

  const verdict   = trust?.ready ? getVerdict(trust.total) : null;
  const credStyle = credibility?.label
    ? CREDIBILITY_STYLE[credibility.label] ?? CREDIBILITY_STYLE["Insufficient Data"]
    : null;

  // Article profile signals
  const sentimentSignal = (() => {
    const s = data?.sentiment_result;
    if (!s) return null;
    const neg = s.negative ?? 0, pos = s.positive ?? 0, neu = s.neutral ?? 0;
    const max = Math.max(neg, pos, neu);
    if (max === neg) return { dotColor: "#ef4444", label: "Sentiment Tone", value: `Negative (${Math.round(neg * 100)}%)`, valueColor: "#991b1b" };
    if (max === pos) return { dotColor: "#10b981", label: "Sentiment Tone", value: `Positive (${Math.round(pos * 100)}%)`, valueColor: "#065f46" };
    return               { dotColor: "#9ca3af", label: "Sentiment Tone", value: `Neutral (${Math.round(neu * 100)}%)`,   valueColor: "#374151" };
  })();

  const emotionSignal = (() => {
    const e = data?.emotion_result;
    if (!e?.dominant_emotion) return null;
    const em = e.dominant_emotion;
    return { dotColor: "#8b5cf6", label: "Dominant emotion", value: `${em.charAt(0).toUpperCase() + em.slice(1)} (${Math.round((e.dominant_score ?? 0) * 100)}%)` };
  })();

  const biasSignal = (() => {
    const b = data?.political_bias_result;
    if (!b?.rating) return null;
    const d = BIAS_DISPLAY[b.rating.toLowerCase()] ?? { label: b.rating, color: "#374151" };
    return { dotColor: d.color, label: "Political bias", value: d.label, valueColor: d.color };
  })();

  return (
    <div
      className="rounded-xl overflow-hidden bg-white transition-all duration-300"
      style={{ boxShadow: `0 0 0 2px ${verdict?.ring ?? "#e5e7eb"}` }}
    >
      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <div className="px-5 pt-5 pb-4" style={{ background: verdict?.bg ?? "#f9fafb" }}>

        {/* Top row */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-1">
              Article Trust Score
            </p>
            {(!trust || !trust.ready) && (
              <div className="animate-pulse w-20 h-12 bg-black/10 rounded" />
            )}
            {trust?.ready && (
              <div className="flex items-baseline gap-1.5">
                <span
                  className="font-sans text-5xl font-bold leading-none"
                  style={{ color: verdict?.color }}
                >
                  {trust.total}
                </span>
                <span className="font-sans text-base text-gray-400">/100</span>
              </div>
            )}
          </div>

          {trust?.ready && verdict && (
            <span
              className="text-xs font-semibold px-3 py-1.5 rounded-full border mt-1 whitespace-nowrap"
              style={{ background: verdict.bg, borderColor: verdict.ring, color: verdict.color }}
            >
              {verdict.emoji} {verdict.label}
            </span>
          )}
          {!trust?.ready && (
            <span className="text-xs font-medium px-3 py-1.5 rounded-full border mt-1 whitespace-nowrap bg-gray-50 border-gray-200 text-gray-400">
              ⏳ Analysing…
            </span>
          )}
        </div>

        {/* Score bar + explanation */}
        {trust?.ready && (
          <>
            <div
              className="w-full h-1.5 rounded-full mb-2.5"
              style={{ background: "rgba(0,0,0,0.10)" }}
            >
              <div
                className="h-1.5 rounded-full transition-all duration-1000"
                style={{ width: `${trust.total}%`, background: verdict?.bar }}
              />
            </div>
            <p className="text-sm leading-relaxed mb-3" style={{ color: verdict?.color, opacity: 0.85 }}>
              {verdict?.explanation}
            </p>
          </>
        )}

        {/* Loading state */}
        {!trust?.ready && trust?.status === "loading" && (
          <div className="space-y-2 mb-3">
            <div className="animate-pulse h-1.5 rounded-full bg-gray-100" />
            <p className="text-xs text-gray-400 leading-relaxed">
              {trust.loadingServices.length === 2
                ? "Waiting for fact-check and propaganda analysis to complete…"
                : `Waiting for ${trust.loadingServices[0]} to complete…`}
            </p>
          </div>
        )}

        {/* Source warning banner — contextual, does not affect score */}
        {trust?.ready && <SourceWarningBanner credibility={credibility} />}

        {/* Breakdown toggle */}
        {trust?.ready && (
          <div className="border-t mt-3 pt-3" style={{ borderColor: "rgba(0,0,0,0.08)" }}>
            <button
              onClick={() => setShowCalc(v => !v)}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full transition-colors cursor-pointer border"
              style={{
                background:   showCalc ? verdict?.bg : "white",
                borderColor:  verdict?.ring ?? "#e5e7eb",
                color:        verdict?.color ?? "#6b7280",
                marginBottom: showCalc ? "0.75rem" : 0,
              }}
            >
              <span>{showCalc ? "▲" : "▼"}</span>
              <span>{showCalc ? "Hide calculation" : "How is this score calculated?"}</span>
            </button>

            {showCalc && (
              <div className="flex flex-col gap-3">
                <ScoreRow label="Fact Accuracy" score={trust.factScore} max={50} icon="✅" />
                <FactPills counts={trust.factCounts} total={trust.factTotal} />
                <ScoreRow label="Low Influence Language" score={trust.propScore} max={50} icon="🧠" />
                <div
                  className="rounded-lg px-3 py-2.5 mt-1"
                  style={{ background: "rgba(0,0,0,0.03)", border: "0.5px solid rgba(0,0,0,0.06)" }}
                >
                  <p className="text-xs text-gray-500 leading-relaxed">
                    <span className="font-semibold text-gray-600">How it's calculated: </span>
                    50 pts for fact accuracy — verified claims score full, unclear claims score half, false claims score zero.
                    50 pts for low influence language. Source credibility is shown as a warning only and does{" "}
                    <em>not</em> affect this number.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── SOURCE CREDIBILITY + ARTICLE PROFILE ──────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-100 border-t border-gray-100 bg-white">

        {/* Source Credibility */}
        <div className="p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">
            Source credibility
          </p>

          {credLoading ? (
            <div className="flex flex-col gap-2">
              {[80, 100, 60].map((w, i) => (
                <div key={i} className="animate-pulse h-3.5 bg-gray-100 rounded" style={{ width: `${w}%` }} />
              ))}
            </div>
          ) : credibility?.status === "ok" ? (
            <>
              <div
                className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 mb-3"
                style={{ background: credStyle?.bg, border: `0.5px solid ${credStyle?.border}` }}
              >
                <span
                  className="rounded-full shrink-0"
                  style={{ width: 7, height: 7, background: credStyle?.dot, display: "inline-block" }}
                />
                <span className="text-xs font-semibold" style={{ color: credStyle?.color }}>
                  {credibility.label}
                </span>
              </div>

              {/* Removed "Score impact" card — no penalty system */}
              <div className="grid grid-cols-2 gap-2">
                {credibility.credibility_score != null && (
                  <MetricCard label="Credibility score" value={`${credibility.credibility_score}/100`} />
                )}
                <MetricCard label="Articles tracked" value={credibility.articles_analyzed} />
                {credibility.factual_accuracy_rate != null && (
                  <MetricCard label="Fact accuracy" value={`${Math.round(credibility.factual_accuracy_rate * 100)}%`} />
                )}
                {credibility.avg_propaganda_probability != null && (
                  <MetricCard
                    label="Average propaganda"
                    value={`${Math.round(credibility.avg_propaganda_probability * 100)}%`}
                    valueColor={credibility.avg_propaganda_probability > 0.5 ? "#991b1b" : undefined}
                  />
                )}
              </div>

              {credibility.articles_analyzed < 10 && (
                <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                  Low sample ({credibility.articles_analyzed} articles) — profile improves as more are analysed.
                </p>
              )}
            </>
          ) : (
            <p className="text-xs text-gray-400 italic">
              {credibility?.status === "no_data"
                ? "No history yet for this source. Submit more articles to build its profile."
                : "Source credibility unavailable."}
            </p>
          )}
        </div>

        {/* Article Profile */}
        <div className="p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">
            Article profile
          </p>

          <div className="flex flex-col gap-1.5">
            {sentimentSignal ? (
              <ProfileRow {...sentimentSignal} />
            ) : (
              <ProfileRowLoading label="Tone" reason="Sentiment analysis running…" />
            )}
            {emotionSignal ? (
              <ProfileRow {...emotionSignal} />
            ) : (
              <ProfileRowLoading label="Dominant emotion" reason="Emotion analysis running…" />
            )}
            {biasSignal ? (
              <ProfileRow {...biasSignal} />
            ) : (
              <ProfileRowLoading label="Political bias" reason="Bias analysis running…" />
            )}
          </div>

          {(sentimentSignal || emotionSignal || biasSignal) && (
            <div className="mt-3 p-2.5 bg-gray-50 rounded-lg border border-gray-100">
              <p className="text-xs text-gray-500 leading-relaxed">
                <span className="font-semibold text-gray-600">Why aren't these in the score? </span>
                Sentiment, emotion, and political bias reflect writing style — not factual accuracy.
                A negative-toned article can still be entirely factual.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TrustSnapshot;