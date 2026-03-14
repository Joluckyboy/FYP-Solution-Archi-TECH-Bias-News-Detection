import { useEffect, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import createSSEConnection from "@/hooks/use-SSE";
import get_api from "@/config/config";

import EmotionTab from "@/components/EmotionTab";
import FactsSummaryBanner from "@/components/FactsSummaryBanner";
import PropagandaTab from "@/components/PropagandaTab";
import PoliticalBias from "@/components/PoliticalBias";
import SentimentTab from "@/components/SentimentTab";

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
  NewspaperIcon, ClipboardList, GlobeLock,
} from "lucide-react";

import "../index.css";

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const FACTUALITY = {
  factual:                "bg-teal-100 text-teal-900",
  "cannot be determined": "bg-amber-100 text-amber-900",
  unfactual:              "bg-rose-100 text-rose-900",
};

const showCites = (fact) => {
  if (!fact.citations?.length) return false;
  const e = (fact.explanation || "").toLowerCase();
  return !["no sources","no source","sources do not","do not mention","does not mention"].some(p => e.includes(p));
};

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────
const ResultsPage = () => {
  const location = useLocation();
  const { id }   = useParams();

  const [data,         setData]         = useState(location.state?.data || null);
  const [API_URL,      setAPI_URL]      = useState(null);
  const [badgeUpdated, setBadgeUpdated] = useState(false);
  const [,             setIsMobile]     = useState(false);
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

  // Trigger data_summary regeneration once per article if summary is missing.
  useEffect(() => {
    if (!API_URL || !data || !data.url) return;
    
    const dataSummary = data.data_summary;
    const hasSummary = dataSummary && typeof dataSummary === 'object' && Object.keys(dataSummary).length > 0;
    
    const articleKey = data.id || data.url;
    if (!articleKey) return;

    // If we have analysis results but no summary, trigger regeneration once.
    if (
      !hasSummary &&
      data.sentiment_result &&
      data.emotion_result &&
      data.propaganda_result &&
      !summaryRegenTriggeredRef.current.has(articleKey)
    ) {
      summaryRegenTriggeredRef.current.add(articleKey);
      console.log('[ResultsPage] Missing data_summary, triggering regeneration...');
      
      fetch(`${API_URL}/application/new_query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: data.url, force: false })
      }).then(() => {
        console.log('[ResultsPage] Data summary regeneration triggered');
      }).catch(err => {
        console.error('[ResultsPage] Failed to trigger summary regeneration:', err);
      });
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

  const emotionSummaryText = data?.data_summary?.emotion_summary
    || "No emotion summary available";
  const propagandaSummaryText = data?.data_summary?.propaganda_summary
    || "No propaganda summary available";
  const sentimentSummaryText = data?.data_summary?.sentiment_summary
    || "No sentiment summary available";

  return (
    <div className="app-container">

      {/* ── Article title card ─────────────────────────────────────────────── */}
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* ── Full article ─────────────────────────────────────────────────── */}
        <Card className="col-span-1 h-[70vh] staggered-slide-in">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <NewspaperIcon strokeWidth={1.5} className="h-8 w-8" />
              <CardTitle className="text-2xl font-base">Full Article</CardTitle>
            </div>
          </CardHeader>
          <ScrollArea className="h-[60vh]">
            <CardContent className="prose max-w-none">
              <p>{data?.content ?? "No content available"}</p>
            </CardContent>
          </ScrollArea>
        </Card>

        <div className="col-span-1 md:col-span-2 space-y-6">

          {/* ── Summary ──────────────────────────────────────────────────────── */}
          <Card className="staggered-slide-in">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <ClipboardList strokeWidth={1.5} className="h-8 w-8" />
                <CardTitle className="text-2xl font-base">Article Summary</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {data?.summarise_result && typeof data.summarise_result === "string" && data.summarise_result.trim() ? (
                <ul className="list-disc ml-6 space-y-2">
                  {data.summarise_result.split("\n\n").filter(p=>p.trim()).map((p,i) => <li key={i}>{p}</li>)}
                </ul>
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

          {/* ── Tabs ─────────────────────────────────────────────────────────── */}
          <Tabs defaultValue="facts" className="w-full slide-in-right">
            <TabsList className="grid w-full grid-cols-5 gap-2 shadow">
              <TabsTrigger value="facts">Facts</TabsTrigger>
              <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
              <TabsTrigger value="emotion">Emotion</TabsTrigger>
              <TabsTrigger value="propaganda">Propaganda</TabsTrigger>
              <TabsTrigger value="politicalbias">Political Bias</TabsTrigger>
            </TabsList>

            {/* ══ FACT-CHECK ══════════════════════════════════════════════════ */}
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
                      <div className="flex items-center">
                        <div className="w-4 h-4 rounded mr-2 bg-teal-100"></div>
                        <span className="text-sm"><b>Factual</b> - Verified with reliable sources</span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-4 h-4 rounded mr-2 bg-amber-100"></div>
                        <span className="text-sm"><b>Cannot be determined</b> - Insufficient evidence</span>
                      </div>
                      <div className="flex items-center">
                        <div className="w-4 h-4 rounded mr-2 bg-rose-100"></div>
                        <span className="text-sm"><b>Unfactual</b> - Contradicts reliable evidence</span>
                      </div>
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
                    <div className="space-y-4">
                      {data.factcheck_result.map((fact, idx) => {
                        const c = fact.correctness ?? "cannot be determined";
                        return (
                          <div key={idx} className="flex items-center space-x-2">
                            <Accordion type="single" collapsible className="w-full">
                              <AccordionItem value={`item-${idx}`}>
                                <AccordionTrigger className={`p-3 rounded-md text-base leading-relaxed ${FACTUALITY[c] ?? FACTUALITY["cannot be determined"]}`}>
                                  <div className="flex items-start">
                                    <span className="mr-2 font-semibold">{idx + 1}.</span>
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
                                        {fact.citations.map((citation, idx) => (
                                          <li key={idx} className="flex items-start space-x-2">
                                            <span className="font-semibold text-blue-600 shrink-0 min-w-[2.5rem]">[{idx + 1}]</span>
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
                    </div>
                  </CardContent>
                )}
              </Card>
            </TabsContent>

            {/* ══ SENTIMENT ══════════════════════════════════════════════════ */}
            <TabsContent value="sentiment">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <BadgeCheck className="h-10 w-10" />
                    <CardTitle className="text-3xl">Sentiment Analysis</CardTitle>
                  </div>
                  <CardDescription>
                    Measures whether the language used in this article is positive, negative, or neutral.
                  </CardDescription>
                  <Accordion type="single" collapsible className="w-full mt-2">
                    <AccordionItem value="s-sum">
                      <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">
                        Summary of this analysis
                      </AccordionTrigger>
                      <AccordionContent className="px-3 pt-2 text-sm text-gray-500">
                        {sentimentSummaryText || "No sentiment summary available"}
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardHeader>
                <Separator />
                <CardContent>
                  <SentimentTab
                    sentimentResult={data.sentiment_result}
                    sentimentSummaryText={sentimentSummaryText}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* ══ EMOTION ════════════════════════════════════════════════════ */}
            <TabsContent value="emotion">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <SmilePlus className="h-10 w-10" />
                    <CardTitle>Emotion Analysis</CardTitle>
                  </div>
                  <CardDescription>
                    Goes deeper than positive/negative — detects specific emotions like fear, approval, or anger.
                  </CardDescription>
                  <Accordion type="single" collapsible className="w-full mt-2">
                    <AccordionItem value="e-sum">
                      <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">
                        Summary of this analysis
                      </AccordionTrigger>
                      <AccordionContent className="px-3 pt-2 text-sm text-gray-500">
                        {emotionSummaryText || "No emotion summary available"}
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardHeader>
                <Separator />
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

            {/* ══ PROPAGANDA ═════════════════════════════════════════════════ */}
            <TabsContent value="propaganda">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Scale className="h-10 w-10" />
                    <CardTitle className="text-3xl">Propaganda Analysis</CardTitle>
                  </div>
                  <CardDescription>
                    Detects language techniques commonly used to influence how readers think or feel.
                  </CardDescription>
                  <Accordion type="single" collapsible className="w-full mt-2">
                    <AccordionItem value="p-sum">
                      <AccordionTrigger className="bg-fuchsia-200 p-2 px-3 rounded font-semibold text-sm">
                        Summary of this analysis
                      </AccordionTrigger>
                      <AccordionContent className="px-3 pt-2 text-sm text-gray-500">
                        {propagandaSummaryText || "No propaganda summary available"}
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardHeader>
                <Separator />
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

            {/* Political Bias Analysis */}
            <TabsContent value="politicalbias">
              <Card className="p-4">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Scale className="h-10 w-10" />
                    <CardTitle className="text-3xl">Political Bias Analysis</CardTitle>
                  </div>
                  <CardDescription>
                    Analyze the political bias of the article.
                    <br />
                    <br />
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <PoliticalBias politicalBiasResult={data.political_bias_result} />
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