import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { get_analyzer } from '@/config/config';
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Sparkles } from "lucide-react";

// Modular Components
import TopicHeader from "@/components/full-coverage/TopicHeader";
import ClusterSummary from "@/components/full-coverage/ClusterSummary";
import MediaBiasChart from "@/components/full-coverage/MediaBiasChart";
import FeaturedCoverageGrid from "@/components/full-coverage/FeaturedCoverageGrid";
import ArticleListSection from "@/components/full-coverage/ArticleListSection";
import CoverageTimeline from "@/components/full-coverage/CoverageTimeline";

const FullCoveragePage = () => {
    const { topicId } = useParams();
    const navigate = useNavigate();
    const [topic, setTopic] = useState(null);
    const [loading, setLoading] = useState(true);
    const [enrichmentLoading, setEnrichmentLoading] = useState(false);
    const [error, setError] = useState(null);
    const [articles, setArticles] = useState([]);
    const [copiedIdx, setCopiedIdx] = useState(null);

    // Always scroll to top when navigating to a new topic
    useEffect(() => {
        window.scrollTo({ top: 0, behavior: 'instant' });
    }, [topicId]);

    useEffect(() => {
        const fetchTopicData = async () => {
            try {
                // 1. Fetch base topic details (fast)
                setLoading(true);
                const ANALYZER_URL = await get_analyzer();
                const baseResponse = await axios.get(`${ANALYZER_URL}/dashboard/topic_details/${topicId}`);
                setTopic(baseResponse.data);
                setArticles(baseResponse.data.articles || []);
                setLoading(false);

                // 2. Fetch LLM-enriched data (slow, background)
                setEnrichmentLoading(true);
                try {
                    const enrichmentResponse = await axios.get(`${ANALYZER_URL}/dashboard/topic_enrichment/${topicId}`);
                    // Merge enrichment into topic
                    setTopic(prev => ({
                        ...prev,
                        ...enrichmentResponse.data
                    }));
                } catch (enrichErr) {
                    console.error("Enrichment failed:", enrichErr);
                } finally {
                    setEnrichmentLoading(false);
                }
            } catch (err) {
                console.error("Failed to fetch topic details:", err);
                setError("Failed to load topic details.");
                setLoading(false);
            }
        };
        if (topicId) fetchTopicData();
    }, [topicId]);

    // ─── Derived metrics ────────────────────────────────────────────────────────
    const getBiasMetrics = () => {
        if (!articles || articles.length === 0) {
            return { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0, total: 0, raw: { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 } };
        }

        const counts = { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 };
        articles.forEach(a => {
            const b = (a.political_bias || a.bias || "").toLowerCase();
            if (b === "left") counts.left++;
            else if (b === "right") counts.right++;
            else if (b === "center") counts.center++;
            else if (b.includes("left")) counts.leaningLeft++;
            else if (b.includes("right")) counts.leaningRight++;
            else counts.center++; // Fallback to center if unclassified
        });

        const total = articles.length;

        return {
            left: Math.round((counts.left / total) * 100),
            leaningLeft: Math.round((counts.leaningLeft / total) * 100),
            center: Math.round((counts.center / total) * 100),
            leaningRight: Math.round((counts.leaningRight / total) * 100),
            right: Math.round((counts.right / total) * 100),
            total,
            raw: counts
        };
    };

    const metrics = getBiasMetrics();

    // ─── Lead articles (backend-computed, with client fallback) ─────────────────
    const getLeadArticle = (biasCategory) => {
        if (topic?.lead_articles?.[biasCategory]) return topic.lead_articles[biasCategory];
        // fallback: first matching article
        return articles.find(a => {
            const b = (a.political_bias || a.bias || "").toLowerCase();
            if (biasCategory === "left") return b.includes("left");
            if (biasCategory === "right") return b.includes("right");
            if (biasCategory === "center") return b.includes("center");
            return false;
        });
    };

    const featuredLeft = getLeadArticle("left");
    const featuredCenter = getLeadArticle("center");
    const featuredRight = getLeadArticle("right");

    // ─── Comparative Coverage Analysis (parsed) ──────────────────────────────────
    const comparativeAnalysis = topic?.comparative_analysis || "";
    const parsedComparative = (() => {
        const result = { left: "", center: "", right: "" };
        if (!comparativeAnalysis) return result;
        const lines = comparativeAnalysis.split("\n").filter(Boolean);
        for (const line of lines) {
            if (/^LEFT:/i.test(line)) result.left = line.replace(/^LEFT:\s*/i, "").trim();
            else if (/^CENTER:/i.test(line)) result.center = line.replace(/^CENTER:\s*/i, "").trim();
            else if (/^RIGHT:/i.test(line)) result.right = line.replace(/^RIGHT:\s*/i, "").trim();
        }
        return result;
    })();

    // ─── Copy handler ────────────────────────────────────────────────────────────
    const handleCopy = (url, idx) => {
        navigator.clipboard.writeText(url).then(() => {
            setCopiedIdx(idx);
            setTimeout(() => setCopiedIdx(null), 2000);
        });
    };

    if (loading) {
        return (
            <div className="container mx-auto p-6 space-y-8">
                <div className="flex bg-white p-4 items-center gap-2">
                    <Skeleton className="h-8 w-8 rounded-full" />
                    <Skeleton className="h-6 w-32" />
                </div>
                <Skeleton className="h-[200px] w-full" />
                <div className="grid grid-cols-3 gap-4">
                    <Skeleton className="h-[300px]" />
                    <Skeleton className="h-[300px]" />
                    <Skeleton className="h-[300px]" />
                </div>
            </div>
        );
    }

    if (error || !topic) {
        return (
            <div className="container mx-auto p-12 text-center text-red-500">
                <h2 className="text-2xl font-bold mb-4">Error Loading Topic</h2>
                <p>{error || "Topic not found"}</p>
                <Button onClick={() => navigate('/')} className="mt-4" variant="outline">Go Back</Button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 font-sans">
            <div className="container mx-auto px-6 py-8 max-w-7xl">
                <TopicHeader title={topic.title} />

                {/* Cluster Summary + Media Bias Chart */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                    <ClusterSummary topic={topic} enrichmentLoading={enrichmentLoading} />
                    <MediaBiasChart topic={topic} articles={articles} metrics={metrics} />
                </div>

                {/* Comparative Coverage Analysis */}
                {(enrichmentLoading || parsedComparative.left || parsedComparative.center || parsedComparative.right) && (
                    <div className="mb-12 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-100">
                            <div className="flex items-center gap-2 flex-wrap">
                                <Sparkles className="h-4 w-4 text-indigo-500" />
                                <h3 className="text-lg font-bold text-slate-800 tracking-tight">Comparative Coverage Analysis</h3>
                                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-xs font-medium text-indigo-600">
                                    <Sparkles className="h-3 w-3" /> AI Generated
                                </span>
                                {enrichmentLoading && <Skeleton className="h-4 w-20 inline-block" />}
                            </div>
                            <p className="text-sm text-slate-500 mb-3">
                                Explore how differently the Left, Center and Right would cover the same piece of news. For perspective(s) lacking in coverage, our AI Analyser will predict how the story would be covered!
                            </p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">
                            {enrichmentLoading && !topic?.comparative_analysis ? (
                                [1, 2, 3].map((i) => (
                                    <div key={i} className="p-5 bg-slate-50/50 space-y-3">
                                        <div className="flex items-center gap-2">
                                            <Skeleton className="h-2 w-2 rounded-full" />
                                            <Skeleton className="h-3 w-24" />
                                        </div>
                                        <Skeleton className="h-4 w-full" />
                                        <Skeleton className="h-4 w-5/6" />
                                    </div>
                                ))
                            ) : (
                                [
                                    { key: "left", label: "Left Framing", headerClass: "text-blue-700", dotClass: "bg-blue-500", bgClass: "bg-blue-100" },
                                    { key: "center", label: "Center Framing", headerClass: "text-purple-600", dotClass: "bg-purple-400", bgClass: "bg-purple-100" },
                                    { key: "right", label: "Right Framing", headerClass: "text-red-700", dotClass: "bg-red-500", bgClass: "bg-red-100" },
                                ].map(({ key, label, headerClass, dotClass, bgClass }) => (
                                    <div key={key} className={`p-5 ${bgClass}`}>
                                        <div className="flex items-center gap-2 mb-3">
                                            <div className={`h-2 w-2 rounded-full ${dotClass}`} />
                                            <p className={`text-xs font-bold uppercase tracking-wider ${headerClass}`}>{label}</p>
                                        </div>
                                        <p className="text-sm text-slate-700 leading-relaxed">
                                            {parsedComparative[key] || <span className="text-slate-400 italic">No data available</span>}
                                        </p>
                                    </div>
                                ))
                            )}
                        </div>
                        <p className="px-6 py-3 text-xs text-slate-400 italic border-t border-slate-100">
                            ✦ This analysis was generated by AI and may not fully represent each outlet's editorial stance.
                        </p>
                    </div>
                )}

                {/* Featured Coverage of Story */}
                <FeaturedCoverageGrid
                    featuredLeft={featuredLeft}
                    featuredCenter={featuredCenter}
                    featuredRight={featuredRight}
                />

                {/* Coverage Timeline */}
                <div className="grid grid-cols-1 gap-8 mb-12">
                    <CoverageTimeline articles={articles} />
                </div>

                {/* Article list */}
                <ArticleListSection
                    articles={articles}
                    topic={topic}
                    enrichmentLoading={enrichmentLoading}
                    copiedIdx={copiedIdx}
                    handleCopy={handleCopy}
                    framingDiff={topic.framing_differences || {}}
                    linguisticFraming={topic.linguistic_framing || {}}
                />
            </div>
        </div>
    );
};

export default FullCoveragePage;
