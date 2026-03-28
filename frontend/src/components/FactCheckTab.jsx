/**
 * FactsSummaryBanner.jsx
 *
 * Renamed intent: this component IS the full Facts tab content.
 * Drop it in and rename to <FactCheckTab> whenever ready.
 *
 * Props:
 *   facts — array of factcheck result objects
 */

import { useState } from "react";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";

// ─── Helpers ──────────────────────────────────────────────────────────────────
const FACTUALITY = {
  factual:                "bg-teal-100 text-teal-900",
  "cannot be determined": "bg-amber-100 text-amber-900",
  unfactual:              "bg-rose-100 text-rose-900",
};

const showCites = (fact) => {
  if (!fact?.citations?.length) return false;
  const e = (fact.explanation || "").toLowerCase();
  return !["no sources", "no source", "sources do not", "do not mention", "does not mention"].some(p => e.includes(p));
};

// ─── Verdict builder ──────────────────────────────────────────────────────────
function buildFactVerdict(facts) {
  if (!Array.isArray(facts) || facts.length === 0) return null;
  const total     = facts.length;
  const factual   = facts.filter(f => (f.correctness ?? "").toLowerCase() === "factual").length;
  const unfactual = facts.filter(f => (f.correctness ?? "").toLowerCase() === "unfactual").length;
  const unclear   = total - factual - unfactual;

  if (unfactual > 0) return {
    style: "bg-rose-50 border-rose-300 text-rose-800", icon: "⚠️",
    counts: { total, factual, unfactual, unclear },
    headline: `${unfactual} claim${unfactual > 1 ? "s" : ""} could not be verified or contradicts available evidence.`,
    sub: "Read the explanations below and check the sources before sharing this article.",
  };
  if (unclear > factual) return {
    style: "bg-amber-50 border-amber-300 text-amber-800", icon: "🔍",
    counts: { total, factual, unfactual, unclear },
    headline: `Most claims (${unclear} of ${total}) could not be independently verified.`,
    sub: "This doesn't mean they're false — just that supporting sources are limited.",
  };
  return {
    style: "bg-teal-50 border-teal-300 text-teal-800", icon: "✅",
    counts: { total, factual, unfactual, unclear },
    headline: `${factual} of ${total} key claim${total > 1 ? "s" : ""} verified with reliable sources.`,
    sub: unclear > 0
      ? `${unclear} claim${unclear > 1 ? "s" : ""} could not be fully verified — see details below.`
      : "No claims were found to contradict available evidence.",
  };
}

// ─── Paginated fact list ──────────────────────────────────────────────────────
function FactCheckList({ facts }) {
  const [shown, setShown] = useState(10);
  if (!Array.isArray(facts) || !facts.length) return null;
  return (
    <div className="space-y-4">
      {facts.slice(0, shown).map((fact, idx) => {
        const c = (fact.correctness ?? "cannot be determined").toLowerCase();
        return (
          <div key={idx} className="flex items-center space-x-2">
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value={`item-${idx}`}>
                <AccordionTrigger
                  className={`p-3 rounded-md text-sm leading-relaxed ${FACTUALITY[c] ?? FACTUALITY["cannot be determined"]}`}
                >
                  <div className="flex items-start">
                    <span className="mr-2 font-semibold shrink-0">{idx + 1}.</span>
                    <span className="text-left">{fact.statement}</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="p-4">
                    <blockquote className="border-l-2 px-4 py-2 italic text-left">
                      <span>{fact.explanation}</span>
                    </blockquote>
                    <br />
                    {showCites(fact) && fact.citation_confidence === "low" && (
                      <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded-md">
                        <p className="text-sm text-amber-700">⚠️ Multiple sources shown — manual verification recommended</p>
                      </div>
                    )}
                    <p className="font-semibold mb-2">Sources:</p>
                    {showCites(fact) ? (
                      <ul className="list-none ml-0 space-y-2 text-gray-700">
                        {fact.citations.map((citation, ci) => (
                          <li key={ci} className="flex items-start space-x-2">
                            <span className="font-semibold text-blue-600 shrink-0 min-w-[2.5rem]">[{ci + 1}]</span>
                            <a href={citation} target="_blank" rel="noopener noreferrer"
                              className="text-blue-600 hover:underline break-all flex items-center gap-1">
                              {citation}
                              <ExternalLink className="h-3 w-3 shrink-0 ml-0.5" />
                            </a>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                        <p className="text-sm text-gray-600 italic">No verifying sources found for this statement</p>
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        );
      })}

      {(shown < facts.length || shown > 10) && (
        <div className="flex items-center justify-between pt-1">
          <p className="text-sm text-gray-400">Showing {Math.min(shown, facts.length)} of {facts.length} claims</p>
          <div className="flex gap-2">
            {shown < facts.length && (
              <button onClick={() => setShown(s => s + 10)}
                className="flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-lg border border-slate-200 bg-white hover:border-indigo-300 hover:text-indigo-600 transition-colors">
                <ChevronDown className="h-4 w-4" /> Show more
              </button>
            )}
            {shown > 10 && (
              <button onClick={() => setShown(10)}
                className="flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors">
                <ChevronUp className="h-4 w-4" /> Show less
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main export ──────────────────────────────────────────────────────────────
const FactsSummaryBanner = ({ facts }) => {
  const verdict     = buildFactVerdict(facts);

  return (
    <div>
        {/* Verdict banner + pills */}
        {verdict && (
          <div className="mb-4 space-y-3">
            <div className={`rounded-lg border px-4 py-3 text-sm font-medium ${verdict.style}`}>
              <p>{verdict.icon} {verdict.headline}</p>
              <p className="text-xs font-normal opacity-80 mt-0.5">{verdict.sub}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="text-xs bg-teal-100 text-teal-700 px-2.5 py-1 rounded-full font-semibold">✅ {verdict.counts.factual} verified</span>
              <span className="text-xs bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full font-semibold">🔍 {verdict.counts.unclear} unclear</span>
              {verdict.counts.unfactual > 0 && (
                <span className="text-xs bg-rose-100 text-rose-700 px-2.5 py-1 rounded-full font-semibold">❌ {verdict.counts.unfactual} unverified</span>
              )}
              <span className="text-xs bg-gray-100 text-gray-500 px-2.5 py-1 rounded-full font-semibold">{verdict.counts.total} total claims</span>
            </div>
          </div>
        )}

        {/* Fact list or loading state */}
        {!Array.isArray(facts) || !facts.length ? (
          <div className="text-center flex flex-col items-center py-8 gap-3">
            <p className="text-sm text-gray-400">Analysis in progress…</p>
            <p className="text-xs text-gray-300">Might take a while depending on article length</p>
          </div>
        ) : (
          <FactCheckList facts={facts} />
        )}
      <Separator className="mt-4" />
    </div>
  );
};

export default FactsSummaryBanner;