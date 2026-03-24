/**
 * PropagandaTab.jsx
 * - Only one technique open at a time
 * - Deduplicates only truly identical sub-clauses (not same paragraph)
 * - Uses technique colours for phrase highlights (matches Full Article)
 * - Uses shared findPhraseInContent from propagandaHighlight.js
 */

import { useState } from "react";
import { cleanPhrase as _cleanPhrase, findPhraseInContent as _findContext } from "@/utils/propagandaHighlight";
import { getHighlightStyle } from "@/utils/highlightPropaganda";

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
        description: TECHNIQUE_DESCRIPTIONS[tag] ?? "An Propaganda technique was detected.",
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

// ─── Phrase with context ──────────────────────────────────────────────────────

function PhraseWithContext({ rawPhrase, articleContent, index, technique }) {
  const ctx            = _findContext(rawPhrase, articleContent);
  const techniqueStyle = getHighlightStyle(technique);

  if (!ctx) return (
    <div className="bg-gray-50 border-l-4 border-gray-300 rounded-r-lg px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mb-1">Detected phrase</p>
      <p className="text-sm text-gray-700 italic">"{_cleanPhrase(rawPhrase)}"</p>
    </div>
  );

  if (!ctx.found) return (
    <div className="bg-gray-50 border-l-4 border-gray-300 rounded-r-lg px-3 py-2 space-y-1">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">Detected phrase</p>
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
        <mark
          className="font-semibold rounded-sm px-0.5"
          style={{ background: techniqueStyle.bg, color: techniqueStyle.color }}
        >
          {ctx.match}
        </mark>
        {ctx.after && <span className="text-gray-400">{ctx.after}</span>}
      </p>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

const PropagandaTab = ({ propScore, articleContent }) => {
  const [openTechnique, setOpenTechnique] = useState(null);

  const toggle = (technique) => {
    setOpenTechnique(prev => prev === technique ? null : technique);
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
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">Propaganda Score</p>
            <p className={`text-3xl font-bold mt-0.5 ${styles.text}`}>{score.toFixed(1)}%</p>
          </div>
          <span className={`text-sm font-bold px-3 py-1 rounded-full border ${styles.badge}`}>
            {severity} Propaganda
          </span>
        </div>

        <div className="w-full bg-gray-100 rounded-full h-3">
          <div className={`${styles.bar} h-3 rounded-full transition-all`} style={{ width: `${score}%` }} />
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-400">
          <span>0% — No Propaganda</span>
          <span>100% — Strong Propaganda</span>
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
          <p className="font-semibold text-gray-600 text-lg">No Propaganda techniques detected</p>
          <p className="text-sm text-center text-gray-400 max-w-sm">
            The article appears to use clear, factual language without recognised persuasion techniques.
          </p>
        </div>
      ) : (
        <div>
          <p className="text-sm font-semibold text-gray-600 mb-1">Detected Techniques</p>
          <p className="text-xs text-gray-400 mb-3">
            {techniques.length} Propaganda technique{techniques.length !== 1 ? "s" : ""} found —
            click any to expand
          </p>

          <div className="flex flex-col gap-2">
            {techniques.map((t) => {
              const isOpen = openTechnique === t.technique;

              // Deduplicate only truly identical sub-clause keys
              // With more aggressive sub-clause splitting, same-paragraph phrases
              // should now resolve to distinct keys
              const seenMatches = new Set();
              const uniquePhrases = t.phrases.filter(phrase => {
                const ctx = _findContext(phrase, articleContent);
                if (!ctx || !ctx.found) return true;
                if (seenMatches.has(ctx.match)) return false;
                seenMatches.add(ctx.match);
                return true;
              });

              return (
                <div
                  key={t.technique}
                  className={`rounded-xl border-2 overflow-hidden transition-all ${isOpen ? "border-blue-400" : "border-gray-200"}`}
                >
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
                        {uniquePhrases.length} instance{uniquePhrases.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <span className="text-gray-400 text-sm">{isOpen ? "▲" : "▼"}</span>
                  </button>

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
                          {uniquePhrases.map((phrase, i) => (
                            <PhraseWithContext
                              key={i}
                              index={i}
                              rawPhrase={phrase}
                              articleContent={articleContent}
                              technique={t.technique}
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