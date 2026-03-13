import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

function _buildFactVerdict(facts) {
  if (!Array.isArray(facts) || facts.length === 0) return null;

  const total     = facts.length;
  const factual   = facts.filter(f => (f.correctness ?? "").toLowerCase() === "factual").length;
  const unfactual = facts.filter(f => (f.correctness ?? "").toLowerCase() === "unfactual").length;
  const unclear   = total - factual - unfactual;

  if (unfactual > 0) {
    return {
      style: "bg-rose-50 border-rose-300 text-rose-800",
      icon: "⚠️",
      counts: { total, factual, unfactual, unclear },
      headline: `${unfactual} claim${unfactual > 1 ? "s" : ""} could not be verified or contradicts available evidence.`,
      sub: "Read the explanations below and check the sources before sharing this article.",
    };
  }

  if (unclear > factual) {
    return {
      style: "bg-amber-50 border-amber-300 text-amber-800",
      icon: "🔍",
      counts: { total, factual, unfactual, unclear },
      headline: `Most claims (${unclear} of ${total}) could not be independently verified.`,
      sub: "This doesn't mean they're false — just that supporting sources are limited.",
    };
  }

  return {
    style: "bg-teal-50 border-teal-300 text-teal-800",
    icon: "✅",
    counts: { total, factual, unfactual, unclear },
    headline: `${factual} of ${total} key claim${total > 1 ? "s" : ""} verified with reliable sources.`,
    sub: unclear > 0
      ? `${unclear} claim${unclear > 1 ? "s" : ""} could not be fully verified — see details below.`
      : "No claims were found to contradict available evidence.",
  };
}

const FactsSummaryBanner = ({ facts, dataSummary }) => {
  const summaryText = dataSummary?.factcheck_summary ?? null;
  const verdict = _buildFactVerdict(facts);

  if (!verdict) return null;

  const { style, icon, counts, headline, sub } = verdict;

  return (
    // px-6 matches CardContent's default horizontal padding so pills line up with claim cards
    <div className="px-6 mb-4 space-y-3">

      {/* AI summary accordion */}
      {summaryText && (
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="fc-sum">
            <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">
              Summary of this analysis
            </AccordionTrigger>
            <AccordionContent className="px-3 pt-2 text-sm text-gray-500">
              {summaryText}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}

      {/* Verdict banner */}
      <div className={`rounded-lg border px-4 py-3 text-sm font-medium ${style}`}>
        <p>{icon} {headline}</p>
        <p className="text-xs font-normal opacity-80 mt-0.5">{sub}</p>
      </div>

      {/* Count pills */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs bg-teal-100 text-teal-700 px-2.5 py-1 rounded-full font-semibold">
          ✅ {counts.factual} verified
        </span>
        <span className="text-xs bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full font-semibold">
          🔍 {counts.unclear} unclear
        </span>
        {counts.unfactual > 0 && (
          <span className="text-xs bg-rose-100 text-rose-700 px-2.5 py-1 rounded-full font-semibold">
            ❌ {counts.unfactual} unverified
          </span>
        )}
        <span className="text-xs bg-gray-100 text-gray-500 px-2.5 py-1 rounded-full font-semibold">
          {counts.total} total claims
        </span>
      </div>

    </div>
  );
};

export default FactsSummaryBanner;