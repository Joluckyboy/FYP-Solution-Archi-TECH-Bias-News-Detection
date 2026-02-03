import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Search, Filter, ExternalLink, Share2, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
        if (!topic || !topic.bias_distribution) return { left: 0, center: 0, right: 0 };
        const dist = topic.bias_distribution;
        const leftRaw = (dist.left || 0) + (dist.leaning_left || 0);
        const rightRaw = (dist.right || 0) + (dist.leaning_right || 0);
        const centerRaw = dist.center || 0;

        const total = leftRaw + rightRaw + centerRaw;
        if (total === 0) return { left: 0, center: 0, right: 0 };

        return {
            left: Math.round((leftRaw / total) * 100),
            center: Math.round((centerRaw / total) * 100),
            right: Math.round((rightRaw / total) * 100),
            total,
            raw: { left: leftRaw, center: centerRaw, right: rightRaw }
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

    // Calculate Alerts
    const silenceAlert = metrics.left < 20 ? "Left" : (metrics.right < 20 ? "Right" : null);
    const consensusScore = metrics.center > 40 ? "HIGH" : (metrics.center < 20 ? "LOW" : "MEDIUM");

    return (
        <div className="min-h-screen bg-slate-50 font-sans">


            <div className="container mx-auto px-6 py-8 max-w-7xl">

                {/* Alerts Section */}
                <div className="flex flex-col md:flex-row gap-6 mb-10 justify-center">
                    {silenceAlert && (
                        <div className="bg-red-100 border border-red-200 p-4 rounded-lg shadow-sm flex-1 max-w-md">
                            <h3 className="font-bold text-red-800 uppercase text-sm mb-1">Silence Alert!</h3>
                            <p className="text-sm text-red-700">
                                Reported significantly less by {silenceAlert}-leaning sources.
                            </p>
                        </div>
                    )}

                    <div className="bg-red-100 border border-red-200 p-4 rounded-lg shadow-sm flex-1 max-w-md">
                        <div className="flex justify-between items-start">
                            <div>
                                <h3 className="font-bold text-red-800 uppercase text-sm mb-1">Consensus Score: {consensusScore}</h3>
                                <p className="text-sm text-red-700">
                                    {consensusScore === "LOW" && "This story is seeing high coverage in Neutral outlets but is likely framed differently across the spectrum."}
                                    {consensusScore === "HIGH" && "Most sources agree on the core facts of this story."}
                                    {consensusScore === "MEDIUM" && "There is moderate agreement across sources."}
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
                        {/* General Summary */}
                        <div className="lg:col-span-2 bg-gray-100 rounded-xl p-6 shadow-inner min-h-[160px] flex items-center justify-center text-gray-500 italic">
                            {/* Placeholder for real summary if available */}
                            &lt; General summary of the clustered topic &gt;
                        </div>

                        {/* Media Bias Chart */}
                        <div className="bg-gray-200 rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-inner">
                            <h3 className="font-semibold text-slate-700 mb-4">Media Bias Chart</h3>

                            {/* Visual representation of L L C R R */}
                            <div className="flex gap-1 w-full max-w-[200px] h-12 items-end justify-center mb-2">
                                <div className={`w-8 rounded-sm ${metrics.raw.left > 0 ? "bg-blue-600" : "bg-gray-300"}`} style={{ height: `${Math.max(20, metrics.left)}%` }} title={`Left: ${metrics.left}%`}></div>
                                <div className={`w-8 rounded-sm ${metrics.raw.left > 0 ? "bg-blue-400" : "bg-gray-300"}`} style={{ height: `${Math.max(20, metrics.left * 0.8)}%` }}></div>
                                <div className={`w-8 rounded-sm ${metrics.raw.center > 0 ? "bg-purple-500" : "bg-gray-300"}`} style={{ height: `${Math.max(20, metrics.center)}%` }} title={`Center: ${metrics.center}%`}></div>
                                <div className={`w-8 rounded-sm ${metrics.raw.right > 0 ? "bg-red-400" : "bg-gray-300"}`} style={{ height: `${Math.max(20, metrics.right * 0.8)}%` }}></div>
                                <div className={`w-8 rounded-sm ${metrics.raw.right > 0 ? "bg-red-600" : "bg-gray-300"}`} style={{ height: `${Math.max(20, metrics.right)}%` }} title={`Right: ${metrics.right}%`}></div>
                            </div>
                            <div className="flex gap-3 text-xs font-mono text-slate-600">
                                <span>L</span><span>L</span><span>C</span><span>R</span><span>R</span>
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
                            <div className="bg-blue-100 border border-blue-200 rounded-lg p-5 flex-1 shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
                                onClick={() => featuredLeft && window.open(featuredLeft.url, '_blank')}>
                                {featuredLeft ? (
                                    <>
                                        <h4 className="text-lg font-semibold text-slate-900 mb-4 group-hover:text-blue-700 leading-snug">
                                            {featuredLeft.title}
                                        </h4>
                                        <div className="mt-auto pt-4 border-t border-blue-200/50">
                                            <p className="font-medium text-slate-700">{featuredLeft.source}</p>
                                        </div>
                                    </>
                                ) : (
                                    <p className="text-slate-500 italic">No left-leaning coverage found.</p>
                                )}
                            </div>
                        </div>

                        {/* Center Coverage */}
                        <div className="flex flex-col">
                            <h3 className="text-center font-medium text-slate-500 mb-2">Center</h3>
                            <div className="bg-white border border-slate-200 rounded-lg p-5 flex-1 shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
                                onClick={() => featuredCenter && window.open(featuredCenter.url, '_blank')}>
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
                                    <p className="text-slate-500 italic">No center coverage found.</p>
                                )}
                            </div>
                        </div>

                        {/* Right Coverage */}
                        <div className="flex flex-col">
                            <h3 className="text-center font-medium text-slate-500 mb-2">Right</h3>
                            <div className="bg-red-100 border border-red-200 rounded-lg p-5 flex-1 shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
                                onClick={() => featuredRight && window.open(featuredRight.url, '_blank')}>
                                {featuredRight ? (
                                    <>
                                        <h4 className="text-lg font-semibold text-slate-900 mb-4 group-hover:text-red-700 leading-snug">
                                            {featuredRight.title}
                                        </h4>
                                        <div className="mt-auto pt-4 border-t border-red-200/50">
                                            <p className="font-medium text-slate-700">{featuredRight.source}</p>
                                        </div>
                                    </>
                                ) : (
                                    <p className="text-slate-500 italic">No right-leaning coverage found.</p>
                                )}
                            </div>
                        </div>

                        {/* Framing Gap / Sidebar */}
                        <div className="hidden lg:flex flex-col justify-center bg-gray-100 rounded-lg p-6">
                            <h3 className="font-semibold text-slate-700 mb-4">Framing Gap</h3>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-600">Left</span>
                                    <span className="w-16 h-2 bg-blue-400 rounded-full"></span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-600">Center</span>
                                    <span className="w-16 h-2 bg-purple-400 rounded-full"></span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-slate-600">Right</span>
                                    <span className="w-16 h-2 bg-red-400 rounded-full"></span>
                                </div>
                                <p className="text-xs text-slate-500 mt-4 italic">
                                    Analysis of how different outlets frame the narrative.
                                </p>
                            </div>
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
                                <button onClick={() => setFilter("left")} className={`${filter === "left" ? "text-blue-600 font-bold" : "text-slate-500 hover:text-slate-800"}`}>
                                    Left ({articles.filter(a => (a.bias || "").toLowerCase().includes("left")).length})
                                </button>
                                <button onClick={() => setFilter("center")} className={`${filter === "center" ? "text-purple-600 font-bold" : "text-slate-500 hover:text-slate-800"}`}>
                                    Center ({articles.filter(a => (a.bias || "").toLowerCase().includes("center")).length})
                                </button>
                                <button onClick={() => setFilter("right")} className={`${filter === "right" ? "text-red-600 font-bold" : "text-slate-500 hover:text-slate-800"}`}>
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
