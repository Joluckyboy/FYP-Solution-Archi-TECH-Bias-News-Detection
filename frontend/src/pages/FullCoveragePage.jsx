import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Search, Filter, ExternalLink, Share2, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const FullCoveragePage = () => {
    const { topicId } = useParams();
    const navigate = useNavigate();
    const [topic, setTopic] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [articles, setArticles] = useState([]);
    const [filter, setFilter] = useState("all"); // all, left, center, right
    const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
        const fetchTopicDetails = async () => {
            try {
                setLoading(true);
                // Ensure this points to your actual backend port
                const response = await axios.get(`http://127.0.0.1:8017/dashboard/topic_details/${topicId}`);
                setTopic(response.data);
                setArticles(response.data.articles || []);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch topic details:", err);
                setError("Failed to load topic details.");
                setLoading(false);
            }
        };

        if (topicId) {
            fetchTopicDetails();
        }
    }, [topicId]);

    // Derived metrics
    const getBiasMetrics = () => {
        if (!topic || !topic.bias_distribution) return { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 };
        const dist = topic.bias_distribution;

        // Raw counts (handling potential missing keys)
        const leftRaw = dist.left || 0;
        const leaningLeftRaw = dist.leaning_left || 0;
        const centerRaw = dist.center || 0;
        const leaningRightRaw = dist.leaning_right || 0;
        const rightRaw = dist.right || 0;

        const total = leftRaw + leaningLeftRaw + centerRaw + leaningRightRaw + rightRaw;
        if (total === 0) return { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 };

        return {
            left: Math.round((leftRaw / total) * 100),
            leaningLeft: Math.round((leaningLeftRaw / total) * 100),
            center: Math.round((centerRaw / total) * 100),
            leaningRight: Math.round((leaningRightRaw / total) * 100),
            right: Math.round((rightRaw / total) * 100),
            total,
            raw: { left: leftRaw, leaningLeft: leaningLeftRaw, center: centerRaw, leaningRight: leaningRightRaw, right: rightRaw }
        };
    };

    const metrics = getBiasMetrics();

    // Featured articles selection (picking top one for each category)
    const getFeaturedArticle = (biasCategory) => {
        return articles.find(a => {
            const b = (a.bias || "").toLowerCase();
            if (biasCategory === "left") return b.includes("left");
            if (biasCategory === "right") return b.includes("right");
            if (biasCategory === "center") return b.includes("center");
            return false;
        });
    };

    const featuredLeft = getFeaturedArticle("left");
    const featuredCenter = getFeaturedArticle("center");
    const featuredRight = getFeaturedArticle("right");

    // Filtering articles
    const filteredArticles = articles.filter(a => {
        const b = (a.bias || "").toLowerCase();
        const title = (a.title || "").toLowerCase();

        // Search filter
        if (searchQuery && !title.includes(searchQuery.toLowerCase())) return false;

        // Category filter
        if (filter === "all") return true;
        if (filter === "left") return b.includes("left");
        if (filter === "right") return b.includes("right");
        if (filter === "center") return b.includes("center");
        return true;
    });

    const getSourceIcon = (source) => {
        // Simple placeholder logic for logos
        return `https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${source?.toLowerCase().replace(/\s/g, '')}.com&size=32`;
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
                <Button onClick={() => navigate(-1)} className="mt-4" variant="outline">
                    Go Back
                </Button>
            </div>
        );
    }

    // Use data from backend or fallback to calculation
    const silenceAlert = topic.polarization_alert || (metrics.left < 20 ? "Left" : (metrics.right < 20 ? "Right" : null));
    // Consensus Score Logic
    let consensusLabel = "MEDIUM";
    let consensusText = "There is moderate agreement across sources.";

    if (topic.consensus_score !== undefined && topic.consensus_score !== null) {
        if (topic.consensus_score > 7) {
            consensusLabel = "HIGH";
            consensusText = "Most sources agree on the core facts of this story.";
        } else if (topic.consensus_score < 4) {
            consensusLabel = "LOW";
            consensusText = "Significant variation in framing across sources.";
        }
    } else {
        // Fallback if no backend score
        if (metrics.center > 40) consensusLabel = "HIGH";
        else if (metrics.center < 20) consensusLabel = "LOW";
    }

    const underReported = topic.under_reported_alert;

    return (
        <div className="min-h-screen bg-slate-50 font-sans">
            <div className="container mx-auto px-6 py-8 max-w-7xl">

                {/* Alerts Section */}
                <div className="flex flex-col md:flex-row gap-6 mb-10 justify-center">
                    {silenceAlert && (
                        <div className="bg-red-100 border border-red-200 p-4 rounded-lg shadow-sm flex-1 max-w-md">
                            <h3 className="font-bold text-red-800 uppercase text-sm mb-1 flex items-center gap-2">
                                <span>🚨</span> Polarization Alert
                            </h3>
                            <p className="text-sm text-red-700">
                                {silenceAlert.includes("skewed") ? silenceAlert : `Reported significantly less by ${silenceAlert}-leaning sources.`}
                            </p>
                        </div>
                    )}

                    {underReported && (
                        <div className="bg-orange-100 border border-orange-200 p-4 rounded-lg shadow-sm flex-1 max-w-md">
                            <h3 className="font-bold text-orange-800 uppercase text-sm mb-1 flex items-center gap-2">
                                <span>🕵️‍♂️</span> Under-Reported
                            </h3>
                            <p className="text-sm text-orange-700">
                                {underReported}
                            </p>
                        </div>
                    )}

                    <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg shadow-sm flex-1 max-w-md">
                        <div className="flex justify-between items-start">
                            <div>
                                <h3 className="font-bold text-blue-800 uppercase text-sm mb-1 flex items-center gap-2">
                                    <span>🤝</span> Consensus Score: {consensusLabel} {topic.consensus_score && `(${topic.consensus_score}/10)`}
                                </h3>
                                <p className="text-sm text-blue-700">
                                    {consensusText}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Topic Header and Summary */}
                <div className="mb-8">
                    <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6 leading-tight">
                        {topic.title}
                    </h1>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Contextual Insight */}
                        <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-slate-100 flex flex-col justify-center">
                            <h3 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
                                <Info className="h-4 w-4 text-blue-500" />
                                AI Contextual Insight
                            </h3>
                            <p className="text-slate-600 text-lg leading-relaxed italic">
                                "{topic.contextual_insight || "Analysis in progress..."}"
                            </p>
                        </div>

                        {/* Media Bias Chart */}
                        <div className="bg-white rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-sm border border-slate-100">
                            <h3 className="font-semibold text-slate-700 mb-6">Media Bias Chart</h3>

                            <div className="w-full flex justify-between h-32 gap-2 px-2">
                                {/* Left */}
                                <div className="flex flex-col items-center justify-end flex-1 gap-2 h-full group">
                                    <span className="text-xs font-medium text-slate-500">{metrics.left}%</span>
                                    <div className={`w-full rounded-t-sm transition-all duration-500 ${metrics.raw.left > 0 ? "bg-blue-700" : "bg-gray-200"}`}
                                        style={{ height: `${Math.max(4, metrics.left)}%` }}
                                        title={`Left: ${metrics.left}%`}></div>
                                    <span className="text-[10px] uppercase font-bold text-slate-400 group-hover:text-blue-700">Left</span>
                                </div>

                                {/* Leaning Left */}
                                <div className="flex flex-col items-center justify-end flex-1 gap-2 h-full group">
                                    <span className="text-xs font-medium text-slate-500">{metrics.leaningLeft}%</span>
                                    <div className={`w-full rounded-t-sm transition-all duration-500 ${metrics.raw.leaningLeft > 0 ? "bg-blue-400" : "bg-gray-200"}`}
                                        style={{ height: `${Math.max(4, metrics.leaningLeft)}%` }}
                                        title={`Leaning Left: ${metrics.leaningLeft}%`}></div>
                                    <span className="text-[10px] uppercase font-bold text-slate-400 group-hover:text-blue-400">L. Left</span>
                                </div>

                                {/* Center */}
                                <div className="flex flex-col items-center justify-end flex-1 gap-2 h-full group">
                                    <span className="text-xs font-medium text-slate-500">{metrics.center}%</span>
                                    <div className={`w-full rounded-t-sm transition-all duration-500 ${metrics.raw.center > 0 ? "bg-purple-500" : "bg-gray-200"}`}
                                        style={{ height: `${Math.max(4, metrics.center)}%` }}
                                        title={`Center: ${metrics.center}%`}></div>
                                    <span className="text-[10px] uppercase font-bold text-slate-400 group-hover:text-purple-500">Center</span>
                                </div>

                                {/* Leaning Right */}
                                <div className="flex flex-col items-center justify-end flex-1 gap-2 h-full group">
                                    <span className="text-xs font-medium text-slate-500">{metrics.leaningRight}%</span>
                                    <div className={`w-full rounded-t-sm transition-all duration-500 ${metrics.raw.leaningRight > 0 ? "bg-red-400" : "bg-gray-200"}`}
                                        style={{ height: `${Math.max(4, metrics.leaningRight)}%` }}
                                        title={`Leaning Right: ${metrics.leaningRight}%`}></div>
                                    <span className="text-[10px] uppercase font-bold text-slate-400 group-hover:text-red-400">L. Right</span>
                                </div>

                                {/* Right */}
                                <div className="flex flex-col items-center justify-end flex-1 gap-2 h-full group">
                                    <span className="text-xs font-medium text-slate-500">{metrics.right}%</span>
                                    <div className={`w-full rounded-t-sm transition-all duration-500 ${metrics.raw.right > 0 ? "bg-red-600" : "bg-gray-200"}`}
                                        style={{ height: `${Math.max(4, metrics.right)}%` }}
                                        title={`Right: ${metrics.right}%`}></div>
                                    <span className="text-[10px] uppercase font-bold text-slate-400 group-hover:text-red-600">Right</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Featured Coverage */}
                <div className="mb-12">
                    <h2 className="text-2xl font-bold text-slate-800 mb-6">Featured Coverage of Story</h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">


                        {/* Left Coverage */}
                        <div className="flex flex-col">
                            <h3 className="text-center font-medium text-slate-500 mb-2">Left</h3>
                            <Card
                                className="bg-red-50 border-red-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer group h-full flex flex-col"
                                onClick={() => featuredLeft && window.open(featuredLeft.url, '_blank')}
                            >
                                <CardContent className="p-5 flex flex-col h-full">
                                    {featuredLeft ? (
                                        <>
                                            <h4 className="text-lg font-semibold text-slate-900 mb-4 group-hover:text-red-700 leading-snug">
                                                {featuredLeft.title}
                                            </h4>
                                            <div className="mt-auto pt-4 border-t border-red-200/50">
                                                <p className="font-medium text-slate-700">{featuredLeft.source}</p>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-slate-500 italic text-sm">
                                            No left-leaning coverage found.
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>

                        {/* Center Coverage */}
                        <div className="flex flex-col">
                            <h3 className="text-center font-medium text-slate-500 mb-2">Center</h3>
                            <Card
                                className="bg-white border-slate-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer group h-full flex flex-col"
                                onClick={() => featuredCenter && window.open(featuredCenter.url, '_blank')}
                            >
                                <CardContent className="p-5 flex flex-col h-full">
                                    {featuredCenter ? (
                                        <>
                                            <h4 className="text-lg font-semibold text-slate-900 mb-4 group-hover:text-purple-700 leading-snug">
                                                {featuredCenter.title}
                                            </h4>
                                            <div className="mt-auto pt-4 border-t border-slate-100">
                                                <p className="font-medium text-slate-700">{featuredCenter.source}</p>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-slate-500 italic text-sm">
                                            No center coverage found.
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>

                        {/* Right Coverage */}
                        <div className="flex flex-col">
                            <h3 className="text-center font-medium text-slate-500 mb-2">Right</h3>
                            <Card
                                className="bg-blue-50 border-blue-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer group h-full flex flex-col"
                                onClick={() => featuredRight && window.open(featuredRight.url, '_blank')}
                            >
                                <CardContent className="p-5 flex flex-col h-full">
                                    {featuredRight ? (
                                        <>
                                            <h4 className="text-lg font-semibold text-slate-900 mb-4 group-hover:text-blue-700 leading-snug">
                                                {featuredRight.title}
                                            </h4>
                                            <div className="mt-auto pt-4 border-t border-blue-200/50">
                                                <p className="font-medium text-slate-700">{featuredRight.source}</p>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-slate-500 italic text-sm">
                                            No right-leaning coverage found.
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>

                        {/* Framing Gap / Sidebar */}
                        <div className="hidden lg:flex flex-col justify-center bg-gray-100 rounded-lg p-6">
                            <h3 className="font-semibold text-slate-700 mb-4">Framing Gap</h3>

                            {topic.framing_gap ? (
                                <div className="space-y-4 text-sm">
                                    <div className="flex flex-col gap-1">
                                        <span className="text-xs font-bold text-red-600 uppercase tracking-wider">Left Sources Use</span>
                                        <div className="flex flex-wrap gap-2">
                                            {topic.framing_gap.left_keywords.map((word, i) => (
                                                <Badge key={i} variant="secondary" className="bg-red-200 text-red-800 hover:bg-red-200">
                                                    "{word}"
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="border-t border-slate-200" />
                                    <div className="flex flex-col gap-1">
                                        <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Right Sources Use</span>
                                        <div className="flex flex-wrap gap-2">
                                            {topic.framing_gap.right_keywords.map((word, i) => (
                                                <Badge key={i} variant="secondary" className="bg-blue-200 text-blue-800 hover:bg-blue-200">
                                                    "{word}"
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-3 text-sm">
                                    <p className="text-slate-500 italic text-xs mb-2">
                                        Not enough data to determine framing differences yet.
                                    </p>
                                    <div className="flex justify-between items-center opacity-50">
                                        <span className="text-slate-600">Left</span>
                                        <span className="w-16 h-2 bg-red-400 rounded-full"></span>
                                    </div>
                                    <div className="flex justify-between items-center opacity-50">
                                        <span className="text-slate-600">Center</span>
                                        <span className="w-16 h-2 bg-purple-400 rounded-full"></span>
                                    </div>
                                    <div className="flex justify-between items-center opacity-50">
                                        <span className="text-slate-600">Right</span>
                                        <span className="w-16 h-2 bg-blue-400 rounded-full"></span>
                                    </div>
                                </div>
                            )}
                        </div>

                    </div>
                </div>

                {/* Article List Section */}
                <div>
                    {/* Controls */}
                    <div className="flex flex-col md:flex-row justify-between items-center mb-6">
                        <div className="flex items-baseline gap-6 mb-4 md:mb-0">
                            <h2 className="text-2xl font-bold text-slate-800">{articles.length} Articles</h2>
                            <div className="flex gap-4 text-sm font-medium">
                                <button onClick={() => setFilter("left")} className={`${filter === "left" ? "text-red-600 font-bold" : "text-slate-500 hover:text-slate-800"}`}>
                                    Left ({articles.filter(a => (a.bias || "").toLowerCase().includes("left")).length})
                                </button>
                                <button onClick={() => setFilter("center")} className={`${filter === "center" ? "text-purple-600 font-bold" : "text-slate-500 hover:text-slate-800"}`}>
                                    Center ({articles.filter(a => (a.bias || "").toLowerCase().includes("center")).length})
                                </button>
                                <button onClick={() => setFilter("right")} className={`${filter === "right" ? "text-blue-600 font-bold" : "text-slate-500 hover:text-slate-800"}`}>
                                    Right ({articles.filter(a => (a.bias || "").toLowerCase().includes("right")).length})
                                </button>
                                {filter !== "all" && (
                                    <button onClick={() => setFilter("all")} className="text-slate-400 hover:text-slate-600 underline">
                                        Clear
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center gap-2 w-full md:w-auto">
                            <div className="relative w-full md:w-64">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search articles..."
                                    className="pl-9 bg-white"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <Button variant="outline" size="icon">
                                <Filter className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>

                    <div className="w-full h-px bg-slate-200 mb-8"></div>

                    {/* Summary Box Redundant? Maybe "Summary from all articles" as in design */}
                    <div className="bg-gray-200 rounded-lg p-6 mb-8 text-center text-slate-600 italic">
                        &lt; summary from all left/centre/right articles &gt;
                    </div>

                    {/* List */}
                    <div className="space-y-4">
                        {filteredArticles.map((article, idx) => (
                            <div key={idx} className="flex gap-4 p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-slate-100 items-start">
                                {/* Logo / Icon */}
                                <div className="h-12 w-12 rounded-full bg-slate-100 flex-shrink-0 overflow-hidden border border-slate-200">
                                    <img
                                        src={getSourceIcon(article.source)}
                                        alt={article.source}
                                        className="h-full w-full object-cover p-2"
                                        onError={(e) => { e.target.src = `https://placehold.co/40x40?text=${article.source?.charAt(0) || "N"}` }}
                                    />
                                </div>

                                <div className="flex-1">
                                    <h3 className="font-semibold text-lg text-slate-900 hover:text-blue-600 cursor-pointer" onClick={() => window.open(article.url, '_blank')}>
                                        {article.title}
                                    </h3>
                                    <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
                                        <span className="font-medium text-slate-700">{article.source}</span>
                                        <span>•</span>
                                        <Badge variant="secondary" className="text-xs uppercase tracking-wider font-normal bg-slate-100 text-slate-600">
                                            {article.bias}
                                        </Badge>
                                        {/* Add Date if available */}
                                    </div>
                                    <p className="text-slate-600 mt-2 text-sm line-clamp-2">
                                        &lt;mini summary&gt;
                                    </p>
                                </div>

                                <div className="flex flex-col gap-2">
                                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => window.open(article.url, '_blank')}>
                                        <ExternalLink className="h-4 w-4 text-slate-400 hover:text-slate-600" />
                                    </Button>
                                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                        <Share2 className="h-4 w-4 text-slate-400 hover:text-slate-600" />
                                    </Button>
                                </div>
                            </div>
                        ))}

                        {filteredArticles.length === 0 && (
                            <div className="text-center py-12 text-slate-500">
                                No articles found matching your criteria.
                            </div>
                        )}
                    </div>

                </div>

            </div>
        </div>
    );
};

export default FullCoveragePage;
