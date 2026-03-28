import { useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Progress } from "@/components/ui/progress";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { HashLoader } from "react-spinners";

// ─── Portal tooltip (not clipped by overflow:hidden parents) ─────────────────
function Tooltip({ text, children }) {
  const ref = useRef(null);
  const [tipPos, setTipPos] = useState(null);

  const show = () => {
    if (!ref.current) return;
    const r = ref.current.getBoundingClientRect();
    setTipPos({ x: r.left + r.width / 2, y: r.top });
  };
  const hide = () => setTipPos(null);

  return (
    <span className="relative inline-flex items-center" ref={ref} onMouseEnter={show} onMouseLeave={hide}>
      {children}
      {tipPos && createPortal(
        <div style={{
          position: "fixed",
          top: tipPos.y - 8,
          left: tipPos.x,
          transform: "translate(-50%, -100%)",
          zIndex: 99999,
          pointerEvents: "none",
          width: 240,
        }}>
          <div className="text-sm" style={{
            background: "#111827",
            color: "#f9fafb",
            lineHeight: 1.5,
            borderRadius: 8,
            padding: "8px 12px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.35)",
            textAlign: "center",
          }}>
            {text}
            <div style={{
              position: "absolute", bottom: -5, left: "50%",
              transform: "translateX(-50%)",
              width: 0, height: 0,
              borderLeft: "5px solid transparent",
              borderRight: "5px solid transparent",
              borderTop: "5px solid #111827",
            }} />
          </div>
        </div>, document.body
      )}
    </span>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
const sentColor = (l) =>
  l === "positive" ? "bg-green-100 border-green-400 text-green-800" :
  l === "negative" ? "bg-red-100 border-red-400 text-red-800" :
                     "bg-amber-100 border-amber-400 text-amber-800";

const sentimentVerdict = (r) => {
  if (!r) return null;
  const neg = r.negative ?? 0, pos = r.positive ?? 0, neu = r.neutral ?? 0;
  if (neg > 0.4)  return { cls: "bg-red-50 border-red-300 text-red-800",       icon: "⚠️", text: `This article leans notably negative (${(neg*100).toFixed(1)}%). Much of the language expresses criticism, conflict, or concern.` };
  if (pos > 0.3)  return { cls: "bg-green-50 border-green-300 text-green-800", icon: "✅", text: `This article leans positive (${(pos*100).toFixed(1)}%). Much of the language is supportive or optimistic.` };
  return            { cls: "bg-blue-50 border-blue-300 text-blue-800",         icon: "📰", text: `This article is mostly neutral (${(neu*100).toFixed(1)}%). It presents information in a balanced, factual tone — typical of news reporting.` };
};

const QUOTE_OPEN  = /^[\u201c\u2018"']/;
const ATTRIBUTION = /[,.]?\s*(he|she|they|mamdani|trump|de blasio|adams|cruz|siles|jessica|tisch|the official|officials?|sources?)\s+(said|wrote|told|added|replied|noted|posted|asked|warned|urged|called|tweeted|announced)/i;
const TRAILING_ATTRIBUTION = /[""'']\s*(,\s*)?(he|she|they|mamdani|trump|adams|cruz|officials?|sources?|the\s+\w+)\s+(said|wrote|told|added|replied|noted|posted)/i;

function isQuotedSpeech(sentence) {
  return QUOTE_OPEN.test(sentence.trim()) ||
         ATTRIBUTION.test(sentence) ||
         TRAILING_ATTRIBUTION.test(sentence);
}

// ─── Component ────────────────────────────────────────────────────────────────
const SentimentTab = ({ sentimentResult }) => {
  const hasSentimentResult = !!(sentimentResult && Object.keys(sentimentResult).length);

  const sentences = sentimentResult?.sentence_sentiments ?? [];
  const POSITIVE_THRESHOLD = 0.15;
  const NEGATIVE_THRESHOLD = 0.15;

  const mostPos = sentences.length
    ? [...sentences].sort((a,b) => b.positive - a.positive)[0]
    : null;
  const mostNeg = sentences.length
    ? [...sentences].sort((a,b) => b.negative - a.negative)[0]
    : null;

  const showMostPos = mostPos && mostPos.positive > POSITIVE_THRESHOLD;
  const showMostNeg = mostNeg && mostNeg.negative > NEGATIVE_THRESHOLD;
  const posCnt    = sentences.filter(s => s.label === "positive").length;
  const negCnt    = sentences.filter(s => s.label === "negative").length;
  const neuCnt    = sentences.filter(s => s.label === "neutral").length;

  const quotedNeg  = sentences.filter(s => s.label === "negative" && isQuotedSpeech(s.sentence)).length;
  const articleNeg = negCnt - quotedNeg;

  const verdict = sentimentVerdict(sentimentResult);

  return (
    <div className="space-y-4">
      {!hasSentimentResult ? (
        <div className="text-center flex flex-col items-center py-8">
          Analysis in progress<br /><br />
          <HashLoader color="#1E5EDD" size={50} />
        </div>
      ) : (
        <>
          {/* Verdict banner */}
          {verdict && (
            <div className={`rounded-lg border px-4 py-3 text-sm font-medium ${verdict.cls}`}>
              {verdict.icon} {verdict.text}
            </div>
          )}

          {/* Score bars */}
          {[
            { key: "positive", tip: "Sentences expressing support, optimism, praise, or agreement." },
            { key: "negative", tip: "Sentences expressing criticism, concern, conflict, or disapproval." },
            { key: "neutral",  tip: "Sentences reporting facts without emotional language." },
          ].map(({ key, tip }) => {
            const val = (sentimentResult[key] ?? 0) * 100;
            return (
              <div key={key} className="space-y-1">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="capitalize text-sm font-medium">
                      {key === "positive" ? "😊 Positive" : key === "negative" ? "😟 Negative" : "😐 Neutral"}
                    </span>
                    <Tooltip text={tip}>
                      <span className="text-sm text-gray-500 bg-gray-100 rounded-full w-[18px] h-[18px] inline-flex items-center justify-center cursor-help border border-gray-300 font-bold select-none">?</span>
                    </Tooltip>
                  </div>
                  <span className="text-sm font-semibold text-gray-600">{val.toFixed(1)}%</span>
                </div>
                <Progress
                  value={val}
                  indicatorClassName={
                    key === "positive" ? "bg-green-300" :
                    key === "neutral"  ? "bg-amber-200" : "bg-red-300"
                  }
                />
              </div>
            );
          })}

          {sentences.length > 0 && (
            <div className="space-y-4 mt-2">
              {/* Count pills + quoted speech note */}
              <div className="space-y-1.5">
                <div className="flex flex-wrap gap-2">
                  <span className="text-sm bg-green-100 text-green-700 px-2.5 py-1 rounded-full font-semibold">😊 {posCnt} positive</span>
                  <span className="text-sm bg-red-100 text-red-700 px-2.5 py-1 rounded-full font-semibold">😟 {negCnt} negative</span>
                  <span className="text-sm bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full font-semibold">😐 {neuCnt} neutral</span>
                </div>

                {quotedNeg > 0 && (
                  <div className="flex items-start gap-1.5 mt-1 p-2 bg-gray-50 border border-gray-200 rounded-lg">
                    <span className="text-sm mt-0.5">💬</span>
                    <p className="text-sm text-gray-500 leading-relaxed">
                      <strong>{quotedNeg} of {negCnt} negative sentences</strong> are direct quotes from people interviewed —
                      not the journalist's own words.
                      {articleNeg > 0
                        ? ` The remaining ${articleNeg} reflect the article's own framing.`
                        : " The article itself uses mostly neutral language."}
                    </p>
                  </div>
                )}

                <p className="text-sm text-gray-400">
                  💡 Percentages show <strong>intensity</strong>, not just count. One strongly neutral sentence outweighs several mildly negative ones.
                </p>
              </div>

              {/* Most positive / most negative */}
              {(showMostPos || showMostNeg) && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {showMostPos && (
                    <div className={`border-l-4 rounded p-3 text-sm ${sentColor("positive")}`}>
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-semibold">Most Positive</p>
                        {isQuotedSpeech(mostPos.sentence) && (
                          <span className="text-sm bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded font-medium">💬 Quoted</span>
                        )}
                      </div>
                      <p className="italic text-sm">"{mostPos.sentence}"</p>
                    </div>
                  )}
                  {showMostNeg && (
                    <div className={`border-l-4 rounded p-3 text-sm ${sentColor("negative")}`}>
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-semibold">Most Negative</p>
                        {isQuotedSpeech(mostNeg.sentence) && (
                          <span className="text-sm bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded font-medium">💬 Quoted</span>
                        )}
                      </div>
                      <p className="italic text-sm">"{mostNeg.sentence}"</p>
                    </div>
                  )}
                </div>
              )}

              {/* Full sentence list */}
              <Accordion type="single" collapsible>
                <AccordionItem value="all-sentences">
                  <AccordionTrigger className="text-sm font-medium">
                    View all {sentences.length} analysed sentences
                  </AccordionTrigger>
                  <AccordionContent>
                    <p className="text-sm text-gray-400 mb-2 px-1">
                      Neutral = reports facts. Positive/Negative = carries emotional weight.
                      <span className="ml-1">💬 = direct quote from a person, not the journalist.</span>
                    </p>
                    <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
                      {sentences.map((s, i) => {
                        const isQuoted = isQuotedSpeech(s.sentence);
                        return (
                          <div key={i} className={`flex items-start gap-2 p-2 rounded border-l-4 text-sm ${sentColor(s.label)}`}>
                            <span className="font-semibold capitalize shrink-0 w-16">{s.label}</span>
                            <span className="flex-1">{s.sentence}</span>
                            {isQuoted && (
                              <span className="text-sm bg-white bg-opacity-70 text-gray-500 px-1 py-0.5 rounded shrink-0 self-start">💬</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SentimentTab;