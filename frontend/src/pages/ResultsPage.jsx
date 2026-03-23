import { useEffect, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import createSSEConnection from "@/hooks/use-SSE";
import get_api from "@/config/config";
import TrustSnapshot from "@/components/TrustSnapshot";
import EmotionTab from "@/components/EmotionTab";
import FactsSummaryBanner from "@/components/FactsSummaryBanner";
import PropagandaTab from "@/components/PropagandaTab";
import PoliticalBias from "@/components/PoliticalBias";
import SentimentTab from "@/components/SentimentTab";
import HighlightedArticle from "@/components/HighlightedArticle";
import RelatedCoverage from "@/components/RelatedCoverage";
import ReactMarkdown from "react-markdown";
import { HashLoader } from "react-spinners";
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import {
  BadgeCheck, Scale, SmilePlus,
  NewspaperIcon, ClipboardList, GlobeLock, ChevronDown, ChevronUp,
} from "lucide-react";

import "../index.css";

// ─── Helpers ──────────────────────────────────────────────────────────────────

const FACTUALITY = {
  factual: "bg-teal-100 text-teal-900",
  "cannot be determined": "bg-amber-100 text-amber-900",
  unfactual: "bg-rose-100 text-rose-900",
};

const showCites = (fact) => {
  if (!fact.citations?.length) return false;
  const e = (fact.explanation || "").toLowerCase();
  return !["no sources", "no source", "sources do not", "do not mention", "does not mention"].some(p => e.includes(p));
};

// ─── Paginated fact-check — shows 10 at a time so 30 claims don't overwhelm ──

function FactCheckList({ facts }) {
  const [shown, setShown] = useState(10);
  if (!Array.isArray(facts) || !facts.length) return null;
  return (
    <div className="space-y-4">
      {facts.slice(0, shown).map((fact, idx) => {
        const c = fact.correctness ?? "cannot be determined";
        return (
          <div key={idx} className="flex items-center space-x-2">
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value={`item-${idx}`}>
                <AccordionTrigger className={`p-3 rounded-md text-base leading-relaxed ${FACTUALITY[c] ?? FACTUALITY["cannot be determined"]}`}>
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
                        <p className="text-sm text-amber-700">⚠️ Multiple sources shown - manual verification recommended</p>
                      </div>
                    )}
                    <p className="font-semibold mb-2">Sources:</p>
                    {showCites(fact) ? (
                      <ul className="list-none ml-0 space-y-2 text-gray-700">
                        {fact.citations.map((citation, ci) => (
                          <li key={ci} className="flex items-start space-x-2">
                            <span className="font-semibold text-blue-600 shrink-0 min-w-[2.5rem]">[{ci + 1}]</span>
                            <a href={citation} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline break-all">{citation}</a>
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

      {/* Show more / less */}
      {(shown < facts.length || shown > 10) && (
        <div className="flex items-center justify-between pt-1">
          <p className="text-sm text-gray-400">
            Showing {Math.min(shown, facts.length)} of {facts.length} claims
          </p>
          <div className="flex gap-2">
            {shown < facts.length && (
              <button
                onClick={() => setShown(s => s + 10)}
                className="flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-lg border border-slate-200 bg-white hover:border-indigo-300 hover:text-indigo-600 transition-colors"
              >
                <ChevronDown className="h-4 w-4" /> Show more
              </button>
            )}
            {shown > 10 && (
              <button
                onClick={() => setShown(10)}
                className="flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors"
              >
                <ChevronUp className="h-4 w-4" /> Show less
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────

const ResultsPage = () => {
  const location = useLocation();
  const { id } = useParams();

  const [data, setData] = useState(location.state?.data || null);
  const [API_URL, setAPI_URL] = useState(null);
  const [badgeUpdated, setBadgeUpdated] = useState(false);
  const [, setIsMobile] = useState(false);
  const summaryRegenTriggeredRef = useRef(new Set());

  useEffect(() => {
    get_api().then(setAPI_URL);
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    if (!API_URL || !id) return;
    const ev = createSSEConnection(API_URL, id, setData);
    return () => ev?.close();
  }, [API_URL, id]);

  useEffect(() => {
    if (!API_URL || !data || !data.url) return;
    const dataSummary = data.data_summary;
    const hasSummary = dataSummary && typeof dataSummary === "object" && Object.keys(dataSummary).length > 0;
    const articleKey = data.id || data.url;
    if (!articleKey) return;
    if (!hasSummary && data.sentiment_result && data.emotion_result && data.propaganda_result
      && !summaryRegenTriggeredRef.current.has(articleKey)) {
      summaryRegenTriggeredRef.current.add(articleKey);
      fetch(`${API_URL}/application/new_query`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: data.url, force: false }),
      }).catch(err => console.error("[ResultsPage] summary regen:", err));
    }
  }, [API_URL, data]);

  useEffect(() => {
    if (!badgeUpdated && data?.propaganda_result?.propaganda_probability !== undefined
      && typeof chrome !== "undefined" && chrome.runtime?.id) {
      chrome.runtime.sendMessage({
        action: "propagandaResultReceived",
        propagandaProbability: data.propaganda_result.propaganda_probability,
        url: data.url || location.state?.articleUrl,
      });
      setBadgeUpdated(true);
    }
  }, [data?.propaganda_result, badgeUpdated, location.state?.articleUrl, data?.url]);

  useEffect(() => {
    document.querySelectorAll(".staggered-slide-in").forEach((el, i) => {
      el.style.transitionDelay = `${i * 0.2}s`;
      el.classList.add("slide-in-top");
    });
  }, [data]);

  if (!data) return (
    <div className="app-container flex items-center justify-center">
      <div className="text-center"><h1>Loading...</h1><br /><HashLoader color="#1E5EDD" size={50} /></div>
    </div>
  );

  const emotionSummaryText = data?.data_summary?.emotion_summary || "No emotion summary available";
  const propagandaSummaryText = data?.data_summary?.propaganda_summary || "No propaganda summary available";
  const sentimentSummaryText = data?.data_summary?.sentiment_summary || "No sentiment summary available";
  const politicalBiasSummaryText = data?.data_summary?.political_bias_summary || "No political bias summary available";

  return (
    <div className="app-container">

      {/* ── Article title card ──────────────────────────────────────────── */}
      <Card className="mb-6 staggered-slide-in">
        <CardHeader>
          <CardTitle className="text-3xl font-bold">{data?.title ?? "No title available"}</CardTitle>
          <div className="flex items-center space-x-2 mt-2 card-subtitle">
            <GlobeLock className="w-4 h-4" />
            <a href={data.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">
              {new URL(data.url).hostname.replace("www.", "")}
            </a>
          </div>
        </CardHeader>
      </Card>

      {/* ── Original 3-column grid ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Left: Full Article */}
        <Card className="col-span-1 h-[70vh] staggered-slide-in">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <NewspaperIcon strokeWidth={1.5} className="h-8 w-8" />
              <CardTitle className="text-2xl font-base">Full Article</CardTitle>
            </div>
          </CardHeader>
          <ScrollArea className="h-[60vh]">
            <CardContent className="prose max-w-none">
              <HighlightedArticle
                content={data?.content}
                propagandaResult={data?.propaganda_result}
              />
            </CardContent>
          </ScrollArea>
        </Card>

        {/* Right: Trust + Summary + Tabs (spans 2 cols) */}
        <div className="col-span-1 md:col-span-2 space-y-6">

          <TrustSnapshot data={data} apiUrl={API_URL} />

          {/* Article Summary */}
          <Card className="staggered-slide-in">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <ClipboardList strokeWidth={1.5} className="h-8 w-8" />
                <CardTitle className="text-2xl font-base">Article Summary</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {data?.summarise_result && typeof data.summarise_result === "string" && data.summarise_result.trim() ? (
                <ReactMarkdown
                  components={{
                    ul: ({ children }) => <ul className="list-disc ml-6 space-y-2 text-sm">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal ml-6 space-y-2 text-sm">{children}</ol>,
                    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                    p: ({ children }) => <p className="text-sm leading-relaxed mb-2">{children}</p>,
                    strong: ({ children }) => <span className="font-semibold text-gray-800">{children}</span>,
                  }}
                >
                  {data.summarise_result}
                </ReactMarkdown>
              ) : data?.summarise_result == null ? (
                <div className="text-center flex flex-col items-center">
                  <br />Analysis in progress<br /><br />
                  <HashLoader color="#1E5EDD" size={50} />
                </div>
              ) : (
                <div className="text-center text-gray-500">No summary available</div>
              )}
            </CardContent>
          </Card>

          {/* ── Analysis Tabs ─────────────────────────────────────────── */}
          {/* 6 tabs: Facts | Sentiment | Emotion | Propaganda | Political Bias | Related */}
          <Tabs defaultValue="facts" className="w-full slide-in-right">
            <TabsList className="hidden md:grid w-full grid-cols-6 gap-1 shadow">
              <TabsTrigger value="facts">Facts</TabsTrigger>
              <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
              <TabsTrigger value="emotion">Emotion</TabsTrigger>
              <TabsTrigger value="propaganda">Propaganda</TabsTrigger>
              <TabsTrigger value="politicalbias">Bias</TabsTrigger>
              <TabsTrigger value="related">Related Coverage</TabsTrigger>
            </TabsList>
            {/* Mobile: scrollable */}
            <TabsList className="flex md:hidden w-full overflow-x-auto flex-nowrap gap-1 h-auto px-1 shadow">
              <TabsTrigger value="facts" className="shrink-0">Facts</TabsTrigger>
              <TabsTrigger value="sentiment" className="shrink-0">Sentiment</TabsTrigger>
              <TabsTrigger value="emotion" className="shrink-0">Emotion</TabsTrigger>
              <TabsTrigger value="propaganda" className="shrink-0">Propaganda</TabsTrigger>
              <TabsTrigger value="politicalbias" className="shrink-0">Bias</TabsTrigger>
              <TabsTrigger value="related" className="shrink-0">Related Coverage</TabsTrigger>
            </TabsList>

            {/* ══ FACT-CHECK ════════════════════════════════════════════ */}
            <TabsContent value="facts">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <BadgeCheck className="h-10 w-10" />
                    <CardTitle className="text-3xl">Fact-Checking</CardTitle>
                  </div>
                  <CardDescription>Key claims from the article, checked against available sources.</CardDescription>
                  <div className="mb-4 rounded-md border p-3 bg-white">
                    <p className="mb-2">Legend:</p>
                    <div className="flex flex-col space-y-2">
                      <div className="flex items-center"><div className="w-4 h-4 rounded mr-2 bg-teal-100" /><span className="text-sm"><b>Factual</b> - Verified with reliable sources</span></div>
                      <div className="flex items-center"><div className="w-4 h-4 rounded mr-2 bg-amber-100" /><span className="text-sm"><b>Cannot be determined</b> - Insufficient evidence</span></div>
                      <div className="flex items-center"><div className="w-4 h-4 rounded mr-2 bg-rose-100" /><span className="text-sm"><b>Unfactual</b> - Contradicts reliable evidence</span></div>
                    </div>
                  </div>
                </CardHeader>
                <Separator className="mb-4" />
                <FactsSummaryBanner facts={data.factcheck_result} dataSummary={data.data_summary} />
                {!Array.isArray(data.factcheck_result) || !data.factcheck_result.length ? (
                  <CardContent>
                    <div className="text-center flex flex-col items-center">
                      <br />Analysis in progress<br /><br />
                      Might take a while depending on article length<br /><br />
                      <HashLoader color="#1E5EDD" size={50} />
                    </div>
                  </CardContent>
                ) : (
                  <CardContent>
                    <FactCheckList facts={data.factcheck_result} />
                  </CardContent>
                )}
              </Card>
            </TabsContent>

            {/* ══ SENTIMENT ═════════════════════════════════════════════ */}
            <TabsContent value="sentiment">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <BadgeCheck className="h-10 w-10" />
                    <CardTitle className="text-3xl">Sentiment Analysis</CardTitle>
                  </div>
                  <CardDescription>Measures whether the language used is positive, negative, or neutral.</CardDescription>
                  <Accordion type="single" collapsible className="w-full mt-2">
                    <AccordionItem value="s-sum">
                      <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                      <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{sentimentSummaryText}</AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardHeader>
                <Separator className="mb-4" />
                <CardContent>
                  <SentimentTab sentimentResult={data.sentiment_result} sentimentSummaryText={sentimentSummaryText} />
                </CardContent>
              </Card>
            </TabsContent>

            {/* ══ EMOTION ═══════════════════════════════════════════════ */}
            <TabsContent value="emotion">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <SmilePlus className="h-10 w-10" />
                    <CardTitle>Emotion Analysis</CardTitle>
                  </div>
                  <CardDescription>Goes deeper than positive/negative — detects emotions like fear, approval, or anger.</CardDescription>
                  <Accordion type="single" collapsible className="w-full mt-2">
                    <AccordionItem value="e-sum">
                      <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                      <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{emotionSummaryText}</AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardHeader>
                <Separator className="mb-4" />
                {!data.emotion_result || !Object.keys(data.emotion_result).length ? (
                  <CardContent>
                    <div className="text-center flex flex-col items-center">
                      <br />Analysis in progress<br /><br />
                      <HashLoader color="#1E5EDD" size={50} />
                    </div>
                  </CardContent>
                ) : (
                  <CardContent>
                    {data.emotion_result?.weighted_avg
                      ? <EmotionTab emotionResult={data.emotion_result} />
                      : <p className="text-gray-500 text-sm">No emotion data available.</p>}
                  </CardContent>
                )}
              </Card>
            </TabsContent>

            {/* ══ PROPAGANDA ════════════════════════════════════════════ */}
            <TabsContent value="propaganda">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Scale className="h-10 w-10" />
                    <CardTitle className="text-3xl">Propaganda Analysis</CardTitle>
                  </div>
                  <CardDescription>Detects language techniques commonly used to influence readers.</CardDescription>
                  <Accordion type="single" collapsible className="w-full mt-2">
                    <AccordionItem value="p-sum">
                      <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                      <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{propagandaSummaryText}</AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardHeader>
                <Separator className="mb-4" />
                {!data.propaganda_result || !Object.keys(data.propaganda_result).length ? (
                  <CardContent>
                    <div className="text-center flex flex-col items-center">
                      <br />Analysis in progress<br /><br />
                      <HashLoader color="#1E5EDD" size={50} />
                    </div>
                  </CardContent>
                ) : (
                  <CardContent>
                    <PropagandaTab propScore={data.propaganda_result} articleContent={data.content} />
                  </CardContent>
                )}
              </Card>
            </TabsContent>

            {/* ══ POLITICAL BIAS ════════════════════════════════════════ */}
            <TabsContent value="politicalbias">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Scale className="h-10 w-10" />
                    <CardTitle className="text-3xl">Political Bias</CardTitle>
                  </div>
                  <CardDescription>Analyses the political leaning and topic framing of the article.</CardDescription>
                  <Accordion type="single" collapsible className="w-full mt-2">
                    <AccordionItem value="b-sum">
                      <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">Summary of this analysis</AccordionTrigger>
                      <AccordionContent className="px-3 pt-2 text-sm text-gray-500">{politicalBiasSummaryText}</AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardHeader>
                <Separator className="mb-4" />
                <CardContent>
                  <PoliticalBias politicalBiasResult={data.political_bias_result} />
                </CardContent>
              </Card>
            </TabsContent>

            {/* ══ RELATED COVERAGE ══════════════════════════════════════ */}
            <TabsContent value="related">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <NewspaperIcon strokeWidth={1.5} className="h-10 w-10" />
                    <CardTitle className="text-3xl">Related Coverage</CardTitle>
                  </div>
                  <CardDescription>
                    Same story covered by other outlets — click <strong>Compare</strong> for a side-by-side analysis.
                  </CardDescription>
                </CardHeader>
                <Separator className="mb-4" />
                <CardContent>
                  {data?.url && API_URL ? (
                    <RelatedCoverage
                      articleUrl={data.url}
                      analysedArticle={data}
                      apiUrl={API_URL}
                      hideHeader
                    />
                  ) : (
                    <div className="text-center py-6 text-slate-400">Loading…</div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;