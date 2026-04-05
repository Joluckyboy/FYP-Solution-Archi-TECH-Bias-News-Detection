import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { get_analyzer } from '@/config/config';
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

// Modular Components
import TopicHeader from "@/components/full-coverage/TopicHeader";
import ClusterSummary from "@/components/full-coverage/ClusterSummary";
import MediaBiasChart from "@/components/full-coverage/MediaBiasChart";
import FeaturedCoverageGrid from "@/components/full-coverage/FeaturedCoverageGrid";
import ArticleListSection from "@/components/full-coverage/ArticleListSection";

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

    // Normalization function for bias
    function getNormalizedBias(article) {
        // Prefer 'lean', then 'leaning', then 'political_bias', then 'bias'
        const raw = article.lean || article.leaning || article.political_bias || article.bias || '';
        const value = raw.toLowerCase().replace(/[_\s]/g, '-');
        if (value === "left") return "left";
        if (value === "right") return "right";
        if (value === "center" || value === "centre") return "center";
        if (value === "lean-left" || value === "leaning-left") return "lean-left";
        if (value === "lean-right" || value === "leaning-right") return "lean-right";
        if (value.includes("left")) return "lean-left";
        if (value.includes("right")) return "lean-right";
        return "center"; // fallback
    }

    const getBiasMetrics = () => {
        if (!articles || articles.length === 0) {
            return { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0, total: 0, raw: { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 } };
        }

        const counts = { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 };
        articles.forEach(a => {
            const b = getNormalizedBias(a);
            if (b === "left") counts.left++;
            else if (b === "right") counts.right++;
            else if (b === "center") counts.center++;
            else if (b === "lean-left") counts.leaningLeft++;
            else if (b === "lean-right") counts.leaningRight++;
            else counts.center++;
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
        const doFallbackCopy = (text) => {
            const textarea = document.createElement("textarea");
            textarea.value = text;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            document.execCommand("copy");
            document.body.removeChild(textarea);
        };

        if (navigator.clipboard && window.isSecureContext) {
            // HTTPS path
            navigator.clipboard.writeText(url).then(() => {
                setCopiedIdx(idx);
                setTimeout(() => setCopiedIdx(null), 2000);
            });
        } else {
            // HTTP fallback (your EC2 case)
            doFallbackCopy(url);
            setCopiedIdx(idx);
            setTimeout(() => setCopiedIdx(null), 2000);
        }
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
            <div className="mx-4 sm:mx-12 py-8">
                <TopicHeader title={topic.title} />

                {/* Cluster Summary + Media Bias Chart */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
                    <ClusterSummary topic={topic} enrichmentLoading={enrichmentLoading} />
                    <MediaBiasChart topic={topic} articles={articles} metrics={metrics} />
                </div>

                {/* Featured Coverage of Story + Comparative Coverage Analysis */}
                <FeaturedCoverageGrid
                    featuredLeft={featuredLeft}
                    featuredCenter={featuredCenter}
                    featuredRight={featuredRight}
                    parsedComparative={parsedComparative}
                    enrichmentLoading={enrichmentLoading}
                />

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
