/**
 * PropagandaTab.jsx
 * - Multiple techniques can be open simultaneously (click to toggle each independently)
 * - Quoted speech note shown for high influence scores
 */

import { useState } from "react";

const SEVERITY_STYLES = {
  Low:      { bar: "bg-green-400",  badge: "bg-green-100 text-green-700 border-green-300",  border: "border-green-400",  text: "text-green-700"  },
  Moderate: { bar: "bg-amber-400",  badge: "bg-amber-100 text-amber-700 border-amber-300",  border: "border-amber-400",  text: "text-amber-700"  },
  High:     { bar: "bg-red-500",    badge: "bg-red-100 text-red-700 border-red-300",         border: "border-red-400",    text: "text-red-700"    },
};

const TECHNIQUE_DESCRIPTIONS = {
  "Name_Calling,Labeling":                       "Attaches a negative or positive label to a person or idea to provoke an emotional reaction without logical argument.",
  "Repetition":                                  "Repeats a message or slogan many times to make it stick in the reader's mind, bypassing critical thinking.",
  "Slogans":                                     "Uses catchy phrases that are easy to remember but oversimplify complex issues.",
  "Appeal_to_fear-prejudice":                    "Exploits fear or existing prejudices to push an agenda, making the audience act out of emotion rather than reason.",
  "Doubt":                                       "Questions the credibility of someone or something to undermine trust without providing evidence.",
  "Exaggeration,Minimisation":                   "Overstates or understates facts to distort reality and steer opinion.",
  "Flag-Waving":                                 "Appeals to national pride or group identity to justify actions or policies.",
  "Loaded_Language":                             "Uses emotionally charged words to influence the audience's feelings toward a subject.",
  "Reductio_ad_hitlerum":                        "Discredits an idea by associating it with an extreme negative figure or group.",
  "Bandwagon":                                   "Implies everyone agrees with a position to pressure others into conforming.",
  "Causal_Oversimplification":                   "Reduces a complex issue to a single cause, ignoring nuance.",
  "Obfuscation,Intentional_Vagueness,Confusion": "Uses unclear or confusing language to hide the true intent of a message.",
  "Appeal_to_Authority":                         "Cites an authority figure to validate a claim, even if they are not an expert on the topic.",
  "Black-and-White_Fallacy":                     "Presents only two extreme options when other possibilities exist.",
  "Thought-terminating_Cliches":                 "Uses familiar phrases to shut down debate and discourage critical thinking.",
  "Red_Herring":                                 "Introduces irrelevant information to distract from the real issue.",
  "Straw_Men":                                   "Misrepresents an opponent's argument to make it easier to attack.",
  "Whataboutism":                                "Deflects criticism by pointing to a different issue, avoiding the original argument.",
};

function formatTechniqueName(name) {
  return name.replace(/_/g, " ").replace(/,/g, " / ");
}

function _deriveTechniques(formattedResult) {
  if (!Array.isArray(formattedResult) || !formattedResult.length) return [];
  const grouped = {};
  for (const item of formattedResult) {
    const tag    = Array.isArray(item) ? item[0] : item.technique;
    const phrase = Array.isArray(item) ? item[1] : item.phrase;
    if (!tag || !phrase) continue;
    if (!grouped[tag]) {
      grouped[tag] = {
        technique:   tag,
        description: TECHNIQUE_DESCRIPTIONS[tag] ?? "An influence technique was detected.",
        phrases:     [],
      };
    }
    grouped[tag].phrases.push(phrase);
  }
  return Object.values(grouped);
}

function _deriveSeverity(probability) {
  if (probability < 0.35) return "Low";
  if (probability < 0.65) return "Moderate";
  return "High";
}

function _cleanPhrase(raw) {
  return raw
    .replace(/(\w)\s'\s(\w)/g, "$1'$2")
    .replace(/\s'\s/g, "'")
    .replace(/##(\w+)/g, "$1")
    .replace(/\s-\s/g, "-")
    .replace(/\s\/\s/g, "/")
    .replace(/,\s+(the\s+)?(official|he|she|they|trump|officials?|sources?|spokesman?)\s+said.*$/i, "")
    .replace(/\s+(the|a|an|and|or|but|of|in|on|at|to|for|with|by|from|as|that|this|also)\s*$/i, "")
    .replace(/\s+([.,;:!?])/g, "$1")
    .replace(/^[\s""''"`.,;:!?()\[\]{}—–]+/, "")
    .replace(/[\s""''"`.,;:!?()\[\]{}—–]+$/, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function _normalizeForMatching(text) {
  return _cleanPhrase(text).toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
}

function _findContext(rawPhrase, articleContent) {
  if (!articleContent || !rawPhrase) return null;

  const cleaned          = _cleanPhrase(rawPhrase);
  const normalizedPhrase = _normalizeForMatching(rawPhrase);
  const phraseTokens     = normalizedPhrase.split(/\s+/).filter(t => t.length > 2);

  if (!phraseTokens.length) return { found: false, cleanPhrase: cleaned };

  const sentences = articleContent
    .split(/(?<=[.!?""''])\s+(?=[A-Z"''])/g)
    .map(s => s.trim())
    .filter(s => s.length > 15);

  if (!sentences.length) return { found: false, cleanPhrase: cleaned };

  let bestSentence = null;
  let bestScore    = 0;

  for (const sentence of sentences) {
    const sentNorm = sentence.toLowerCase().replace(/[^a-z0-9\s]/g, " ");
    const score    = phraseTokens.filter(tok => sentNorm.includes(tok)).length;
    if (score > bestScore) { bestScore = score; bestSentence = sentence; }
  }

  const minScore = Math.max(1, Math.floor(phraseTokens.length * 0.4));
  if (!bestSentence || bestScore < minScore) return { found: false, cleanPhrase: cleaned };

  const sentLower      = bestSentence.toLowerCase().replace(/[^a-z0-9\s]/g, " ");
  const tokenPositions = [];

  for (const tok of phraseTokens) {
    let searchFrom = 0;
    while (true) {
      const idx = sentLower.indexOf(tok, searchFrom);
      if (idx === -1) break;
      tokenPositions.push({ start: idx, end: idx + tok.length, tok });
      searchFrom = idx + 1;
    }
  }

  if (!tokenPositions.length) return { found: false, cleanPhrase: cleaned };

  tokenPositions.sort((a, b) => a.start - b.start);

  const windowSize = Math.min(phraseTokens.length, tokenPositions.length);
  let bestStart  = tokenPositions[0].start;
  let bestEnd    = tokenPositions[windowSize - 1].end;
  let bestSpan   = bestEnd - bestStart;
  let bestUnique = new Set(tokenPositions.slice(0, windowSize).map(p => p.tok)).size;

  for (let i = 1; i <= tokenPositions.length - windowSize; i++) {
    const wp      = tokenPositions.slice(i, i + windowSize);
    const wStart  = wp[0].start;
    const wEnd    = wp[windowSize - 1].end;
    const wSpan   = wEnd - wStart;
    const wUnique = new Set(wp.map(p => p.tok)).size;
    if (wUnique > bestUnique || (wUnique === bestUnique && wSpan < bestSpan)) {
      bestStart = wStart; bestEnd = wEnd; bestSpan = wSpan; bestUnique = wUnique;
    }
  }

  if (bestEnd - bestStart > 120) {
    const anchor = tokenPositions[0];
    bestStart    = anchor.start;
    const words  = sentLower.slice(anchor.start).split(/\s+/).slice(0, phraseTokens.length + 2).join(" ");
    bestEnd      = anchor.start + words.length;
  }

  let highlightStart = Math.max(0, bestStart);
  let highlightEnd   = Math.min(bestSentence.length, bestEnd);

  while (highlightStart > 0 && !/\s/.test(bestSentence[highlightStart - 1])) highlightStart--;
  while (highlightEnd < bestSentence.length && !/\s/.test(bestSentence[highlightEnd])) highlightEnd++;

  const before = bestSentence.slice(0, highlightStart);
  const match  = bestSentence.slice(highlightStart, highlightEnd);
  const after  = bestSentence.slice(highlightEnd);

  if (!match.trim()) return { found: false, cleanPhrase: cleaned };
  return { found: true, before, match, after };
}

function PhraseWithContext({ rawPhrase, articleContent, index }) {
  const ctx = _findContext(rawPhrase, articleContent);

  if (!ctx) return (
    <div className="bg-amber-50 border-l-4 border-amber-400 rounded-r-lg px-3 py-2">
      <p className="text-sm text-gray-700 italic">"{_cleanPhrase(rawPhrase)}"</p>
    </div>
  );

  if (!ctx.found) return (
    <div className="bg-amber-50 border-l-4 border-amber-400 rounded-r-lg px-3 py-2 space-y-1">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-600">Detected phrase</p>
      <p className="text-sm text-gray-700 italic">"{ctx.cleanPhrase}"</p>
    </div>
  );

  return (
    <div className="bg-amber-50 border-l-4 border-amber-400 rounded-r-lg px-3 py-2.5 space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-600">
        Instance {index + 1} — in context
      </p>
      <p className="text-sm text-gray-700 leading-relaxed">
        {ctx.before && <span className="text-gray-400">{ctx.before}</span>}
        <mark className="bg-amber-300 text-amber-900 font-semibold rounded-sm px-0.5">{ctx.match}</mark>
        {ctx.after && <span className="text-gray-400">{ctx.after}</span>}
      </p>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

const PropagandaTab = ({ propScore, articleContent }) => {
  // ← KEY CHANGE: Set instead of single value — multiple open at once
  const [openSet, setOpenSet] = useState(new Set());

  const toggle = (technique) => {
    setOpenSet(prev => {
      const next = new Set(prev);
      next.has(technique) ? next.delete(technique) : next.add(technique);
      return next;
    });
  };

  if (!propScore) return null;

  const score    = (propScore.propaganda_probability ?? 0) * 100;
  const severity = propScore.severity ?? _deriveSeverity(propScore.propaganda_probability ?? 0);
  const styles   = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.Moderate;
  const coverage = propScore.coverage_pct ?? null;

  const techniques =
    Array.isArray(propScore.techniques) && propScore.techniques.length > 0
      ? propScore.techniques
      : _deriveTechniques(propScore.formatted_result ?? []);

  return (
    <div className="space-y-6">

      {/* ── Influence Score ── */}
      <div className={`rounded-xl border-2 p-5 bg-white ${styles.border}`}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">Influence Score</p>
            <p className={`text-3xl font-bold mt-0.5 ${styles.text}`}>{score.toFixed(1)}%</p>
          </div>
          <span className={`text-sm font-bold px-3 py-1 rounded-full border ${styles.badge}`}>
            {severity} Influence
          </span>
        </div>

        <div className="w-full bg-gray-100 rounded-full h-3">
          <div className={`${styles.bar} h-3 rounded-full transition-all`} style={{ width: `${score}%` }} />
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-400">
          <span>0% — No influence</span>
          <span>100% — Strong influence</span>
        </div>

        <p className="text-sm text-gray-500 mt-3 border-t pt-3">
          {severity === "Low"      && "💬 This article appears to use mostly straightforward, factual language."}
          {severity === "Moderate" && "💬 This article contains some language that may be intended to influence opinions."}
          {severity === "High"     && "💬 This article contains strong language patterns commonly used to shape or manipulate opinion."}
        </p>

        {coverage !== null && (
          <p className="text-xs text-gray-400 mt-1">
            Influence language detected in approximately {coverage}% of the article's content.
          </p>
        )}

        {score >= 60 && (
          <div className="mt-3 flex items-start gap-2 p-2.5 bg-gray-50 border border-gray-200 rounded-lg">
            <span className="text-sm shrink-0">💬</span>
            <p className="text-xs text-gray-500 leading-relaxed">
              <strong>Note:</strong> Quoted speech from people interviewed can raise this score
              even when the journalist's own language is neutral. Check the highlighted
              instances below to see whether the techniques appear in quotes or in the
              article's own writing.
            </p>
          </div>
        )}
      </div>

      {/* ── Techniques ── */}
      {techniques.length === 0 ? (
        <div className="flex flex-col items-center py-10 text-gray-400 space-y-2">
          <span className="text-5xl">✅</span>
          <p className="font-semibold text-gray-600 text-lg">No influence techniques detected</p>
          <p className="text-sm text-center text-gray-400 max-w-sm">
            The article appears to use clear, factual language without recognised persuasion techniques.
          </p>
        </div>
      ) : (
        <div>
          <p className="text-sm font-semibold text-gray-600 mb-1">Detected Techniques</p>
          <p className="text-xs text-gray-400 mb-3">
            {techniques.length} influence technique{techniques.length !== 1 ? "s" : ""} found —
            click any to expand, open multiple at once
          </p>

          <div className="flex flex-col gap-2">
            {techniques.map((t) => {
              const isOpen = openSet.has(t.technique);
              return (
                <div
                  key={t.technique}
                  className={`rounded-xl border-2 overflow-hidden transition-all ${isOpen ? "border-blue-400" : "border-gray-200"}`}
                >
                  {/* Toggle button */}
                  <button
                    className={`w-full text-left px-4 py-3 flex items-center justify-between transition-colors ${
                      isOpen ? "bg-blue-50" : "bg-gray-50 hover:bg-gray-100"
                    }`}
                    onClick={() => toggle(t.technique)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-sm text-gray-800">
                        {formatTechniqueName(t.technique)}
                      </span>
                      <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                        {t.phrases.length} instance{t.phrases.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <span className="text-gray-400 text-sm">{isOpen ? "▲" : "▼"}</span>
                  </button>

                  {/* Content — visible when open */}
                  {isOpen && (
                    <div className="px-4 py-4 bg-white space-y-4 border-t border-blue-100">
                      <div>
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">What is this?</p>
                        <p className="text-sm text-gray-700">{t.description}</p>
                      </div>

                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                            Found in this article
                          </p>
                          {articleContent && (
                            <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-medium">
                              highlighted in context
                            </span>
                          )}
                        </div>
                        <div className="space-y-2">
                          {t.phrases.map((phrase, i) => (
                            <PhraseWithContext
                              key={i}
                              index={i}
                              rawPhrase={phrase}
                              articleContent={articleContent}
                            />
                          ))}
                        </div>
                      </div>

                      <div className="pt-2 border-t border-gray-100">
                        <p className="text-xs text-gray-400 italic">
                          💡 Ask yourself: does knowing this technique is present change how you read this content?
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default PropagandaTab;