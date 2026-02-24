import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { ANALYZER_URL } from '@/config/config';
import { Search, Filter, Copy, Info, Eye, EyeOff, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

const FullCoveragePage = () => {
    const { topicId } = useParams();
    const navigate = useNavigate();
    const [topic, setTopic] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [articles, setArticles] = useState([]);
    const [filter, setFilter] = useState("all");
    const [searchQuery, setSearchQuery] = useState("");
    const [copiedIdx, setCopiedIdx] = useState(null);

    useEffect(() => {
        const fetchTopicDetails = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`${ANALYZER_URL}/dashboard/topic_details/${topicId}`);
                setTopic(response.data);
                setArticles(response.data.articles || []);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch topic details:", err);
                setError("Failed to load topic details.");
                setLoading(false);
            }
        };
        if (topicId) fetchTopicDetails();
    }, [topicId]);

    // ─── Derived metrics ────────────────────────────────────────────────────────
    const getBiasMetrics = () => {
        if (!topic || !topic.bias_distribution) return { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0, total: 0, raw: { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 } };
        const dist = topic.bias_distribution;
        const leftRaw = dist.left || 0;
        const leaningLeftRaw = dist.leaning_left || 0;
        const centerRaw = dist.center || 0;
        const leaningRightRaw = dist.leaning_right || 0;
        const rightRaw = dist.right || 0;
        const total = leftRaw + leaningLeftRaw + centerRaw + leaningRightRaw + rightRaw;
        if (total === 0) return { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0, total: 0, raw: { left: 0, leaningLeft: 0, center: 0, leaningRight: 0, right: 0 } };
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

    // ─── Filter ──────────────────────────────────────────────────────────────────
    const filteredArticles = articles.filter(a => {
        const b = (a.political_bias || a.bias || "").toLowerCase();
        const title = (a.title || "").toLowerCase();
        if (searchQuery && !title.includes(searchQuery.toLowerCase())) return false;
        if (filter === "all") return true;
        if (filter === "left") return b.includes("left");
        if (filter === "right") return b.includes("right");
        if (filter === "center") return b.includes("center");
        return true;
    });

    const getSourceIcon = (source) =>
        `https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${source?.toLowerCase().replace(/\s/g, '')}.com&size=32`;


    // ─── Copy handler ────────────────────────────────────────────────────────────
    const handleCopy = (url, idx) => {
        navigator.clipboard.writeText(url).then(() => {
            setCopiedIdx(idx);
            setTimeout(() => setCopiedIdx(null), 2000);
        });
    };

    // ─── Bias display helpers ─────────────────────────────────────────────────────
    const getBiasLabel = (rawBias) => {
        const b = (rawBias || "").toLowerCase();
        if (b === "left") return { label: "Left", color: "bg-red-600 text-white" };
        if (b.includes("leaning") && b.includes("left")) return { label: "Lean Left", color: "bg-red-400 text-white" };
        if (b === "center") return { label: "Center", color: "bg-slate-400 text-white" };
        if (b.includes("leaning") && b.includes("right")) return { label: "Lean Right", color: "bg-blue-400 text-white" };
        if (b === "right") return { label: "Right", color: "bg-blue-700 text-white" };
        return { label: rawBias || "Unknown", color: "bg-slate-200 text-slate-700" };
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

    const silentOutlets = topic.silent_outlets || {};
    const framingDiff = topic.framing_differences || {};
    const linguisticFraming = topic.linguistic_framing || {};
    const comparativeAnalysis = topic.comparative_analysis || "";

    // Parse comparative_analysis text into { left, center, right } sentences
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

    return (
        <div className="min-h-screen bg-slate-50 font-sans">
            <div className="container mx-auto px-6 py-8 max-w-7xl">

                {/* ── Topic Header ──────────────────────────────────────────────── */}
                <div className="mb-8">
                    <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6 leading-tight">
                        {topic.title}
                    </h1>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                        {/* Daily Briefing card */}
                        <div className="lg:col-span-2 relative overflow-hidden rounded-xl border border-slate-200 shadow-sm bg-white">
                            <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600" />
                            <div className="p-6 md:p-8">
                                <div className="flex items-center gap-2 mb-4">
                                    <div className="p-2 bg-blue-50 rounded-lg">
                                        <Info className="h-5 w-5 text-blue-600" />
                                    </div>
                                    <h3 className="text-lg font-bold text-slate-800">Daily Briefing &amp; AI Analysis</h3>
                                </div>

                                {/* ── Feature 2: Silent Outlets alerts ── */}
                                {(silentOutlets.left_silent || silentOutlets.right_silent || silentOutlets.center_silent) && (
                                    <div className="mb-4 space-y-2">
                                        {silentOutlets.left_silent && (
                                            <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                                                <EyeOff className="h-4 w-4 flex-shrink-0" />
                                                <span><strong>Left outlets are silent</strong> — this story has no left-leaning coverage despite significant attention elsewhere.</span>
                                            </div>
                                        )}
                                        {silentOutlets.right_silent && (
                                            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                                                <EyeOff className="h-4 w-4 flex-shrink-0" />
                                                <span><strong>Right outlets are silent</strong> — this story has no right-leaning coverage despite significant attention elsewhere.</span>
                                            </div>
                                        )}
                                        {silentOutlets.center_silent && (
                                            <div className="flex items-center gap-2 p-3 bg-purple-50 border border-purple-200 rounded-lg text-sm text-purple-800">
                                                <EyeOff className="h-4 w-4 flex-shrink-0" />
                                                <span><strong>Center outlets are silent</strong> — no centrist coverage found for this story.</span>
                                            </div>
                                        )}
                                    </div>
                                )}

                                <div className="space-y-6">
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Event Summary</h4>
                                        <p className="text-slate-900 text-lg leading-relaxed whitespace-pre-line">
                                            {(topic.contextual_insight || "Analysis in progress...").split(/coverage analysis:/i)[0].trim()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Media Bias Chart */}
                        <div className="bg-white rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-sm border border-slate-100">
                            <h3 className="font-semibold text-slate-700 mb-6">Media Bias Chart</h3>

                            <div className="w-full flex justify-between h-32 gap-2 px-2">
                                {[
                                    { key: "left", label: "Left", pct: metrics.left, hasData: metrics.raw.left > 0, barColor: "bg-red-600" },
                                    { key: "leaningLeft", label: "L. Left", pct: metrics.leaningLeft, hasData: metrics.raw.leaningLeft > 0, barColor: "bg-red-400" },
                                    { key: "center", label: "Center", pct: metrics.center, hasData: metrics.raw.center > 0, barColor: "bg-slate-400" },
                                    { key: "leaningRight", label: "L. Right", pct: metrics.leaningRight, hasData: metrics.raw.leaningRight > 0, barColor: "bg-blue-400" },
                                    { key: "right", label: "Right", pct: metrics.right, hasData: metrics.raw.right > 0, barColor: "bg-blue-700" },
                                ].map(({ key, label, pct, hasData, barColor }) => (
                                    <div key={key} className="flex flex-col items-center justify-end flex-1 gap-2 h-full group">
                                        <span className="text-xs font-medium text-slate-500">{pct}%</span>
                                        <div className={`w-full rounded-t-sm transition-all duration-500 ${hasData ? barColor : "bg-gray-200"}`}
                                            style={{ height: `${Math.max(4, pct)}%` }}
                                            title={`${label}: ${pct}%`} />
                                        <span className="text-[10px] uppercase font-bold text-slate-400">{label}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Polarization Analysis — icon + outlet name pills  */}
                            <div className="mt-8 pt-6 border-t border-slate-100 w-full">
                                <h4 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wide">Polarization Analysis</h4>
                                {(() => {
                                    const uniqueSources = {};
                                    articles.forEach(a => {
                                        if (a.source && !uniqueSources[a.source]) {
                                            uniqueSources[a.source] = {
                                                source: a.source,
                                                bias: (a.political_bias || a.bias || "").toLowerCase()
                                            };
                                        }
                                    });
                                    const sources = Object.values(uniqueSources);
                                    return (
                                        <div className="flex flex-col items-center">
                                            <p className="text-sm text-slate-500 mb-4">
                                                This story is covered by <span className="font-bold text-slate-800">{sources.length}</span> unique sources.
                                            </p>
                                            <div className="flex flex-wrap justify-center gap-2">
                                                {sources.map((s, i) => {
                                                    let pillClass = "bg-slate-100 border-slate-200 text-slate-700";
                                                    if (s.bias.includes("left")) pillClass = "bg-red-100 border-red-200 text-red-800";
                                                    else if (s.bias.includes("right")) pillClass = "bg-blue-100 border-blue-200 text-blue-800";
                                                    else if (s.bias.includes("center")) pillClass = "bg-grey-100 border-grey-200 text-grey-800";

                                                    return (
                                                        <div key={i} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${pillClass}`}
                                                            title={`${s.source} (${s.bias})`}>
                                                            <img
                                                                src={getSourceIcon(s.source)}
                                                                alt={s.source}
                                                                className="h-4 w-4 rounded-full object-cover flex-shrink-0"
                                                                onError={(e) => { e.target.style.display = 'none'; }}
                                                            />
                                                            <span className="max-w-[80px] truncate">{s.source}</span>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    );
                                })()}
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Featured Coverage ─────────────────────────────────────────── */}
                <div className="mb-12">
                    <h2 className="text-2xl font-bold text-slate-800 mb-6">Featured Coverage of Story</h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {[
                            { label: "Left", article: featuredLeft, cardClass: "bg-red-50 border-red-200", hoverColor: "group-hover:text-red-700", dividerColor: "border-red-200/50", emptyMsg: "No left-leaning coverage found." },
                            { label: "Center", article: featuredCenter, cardClass: "bg-white border-slate-200", hoverColor: "group-hover:text-purple-700", dividerColor: "border-slate-100", emptyMsg: "No center coverage found." },
                            { label: "Right", article: featuredRight, cardClass: "bg-blue-50 border-blue-200", hoverColor: "group-hover:text-blue-700", dividerColor: "border-blue-200/50", emptyMsg: "No right-leaning coverage found." },
                        ].map(({ label, article, cardClass, hoverColor, dividerColor, emptyMsg }) => (
                            <div key={label} className="flex flex-col">
                                <h3 className="text-center font-medium text-slate-500 mb-2">{label}</h3>
                                <Card className={`${cardClass} shadow-sm hover:shadow-md transition-shadow cursor-pointer group h-full flex flex-col`}
                                    onClick={() => article && window.open(article.url, '_blank')}>
                                    <CardContent className="p-5 flex flex-col h-full">
                                        {article ? (
                                            <>
                                                <h4 className={`text-lg font-semibold text-slate-900 mb-3 ${hoverColor} leading-snug`}>
                                                    {article.title}
                                                </h4>
                                                {article.summary && (
                                                    <p className="text-sm text-slate-600 line-clamp-3 mb-3">{article.summary}</p>
                                                )}
                                                <div className={`mt-auto pt-4 border-t ${dividerColor} flex items-center justify-between`}>
                                                    <p className="font-medium text-slate-700 text-sm">{article.source}</p>
                                                    {article.published_at && (
                                                        <span className="text-xs text-slate-400">{String(article.published_at).slice(0, 10)}</span>
                                                    )}
                                                </div>
                                            </>
                                        ) : (
                                            <div className="flex items-center justify-center h-full text-slate-500 italic text-sm">{emptyMsg}</div>
                                        )}
                                    </CardContent>
                                </Card>
                            </div>
                        ))}
                    </div>

                    {/* ── Framing Differences panel ── */}
                    {(framingDiff.left?.length > 0 || framingDiff.center?.length > 0 || framingDiff.right?.length > 0 || linguisticFraming.left || linguisticFraming.center || linguisticFraming.right) && (
                        <div className="mt-6 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
                                <Eye className="h-4 w-4 text-slate-500" />
                                <h3 className="font-semibold text-slate-700">Framing Differences in Headline</h3>
                                <span className="text-xs text-slate-400 ml-1">— distinctive keywords each political leaning focuses on</span>
                            </div>
                            <div className="grid grid-cols-3 divide-x divide-slate-100">
                                {[
                                    { key: "left", label: "Left Coverage", headerClass: "text-red-700 bg-red-50", badgeClass: "bg-red-100 text-red-800", barColor: "bg-red-500" },
                                    { key: "center", label: "Center Coverage", headerClass: "text-slate-600 bg-slate-50", badgeClass: "bg-slate-200 text-slate-700", barColor: "bg-slate-400" },
                                    { key: "right", label: "Right Coverage", headerClass: "text-blue-700 bg-blue-50", badgeClass: "bg-blue-100 text-blue-800", barColor: "bg-blue-500" },
                                ].map(({ key, label, headerClass, badgeClass, barColor }) => {
                                    const lf = linguisticFraming[key] || {};
                                    const passivePct = lf.passive_pct ?? null;
                                    const activePct = lf.active_pct ?? null;
                                    const topAgents = lf.top_agents || [];
                                    return (
                                        <div key={key}>
                                            <div className={`px-4 py-2 text-xs font-bold uppercase tracking-wider ${headerClass}`}>{label}</div>
                                            {/* Keyword badges */}
                                            <div className="px-4 pt-4 pb-2 flex flex-wrap gap-2 min-h-[60px]">
                                                {(framingDiff[key] || []).length > 0
                                                    ? framingDiff[key].map((word, i) => (
                                                        <span key={i} className={`px-2.5 py-1 rounded-full text-xs font-semibold ${badgeClass}`}>{word}</span>
                                                    ))
                                                    : <span className="text-xs text-slate-400 italic">Not enough data</span>
                                                }
                                            </div>
                                            {/* Passive / Active voice bar */}
                                            {passivePct !== null && (
                                                <div className="px-4 pb-4 pt-1">
                                                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                                                        <span>Active <span className="font-semibold">{activePct}%</span></span>
                                                        <span>Passive <span className="font-semibold">{passivePct}%</span></span>
                                                    </div>
                                                    <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                                                        <div className={`h-full rounded-full ${barColor} opacity-70`} style={{ width: `${activePct}%` }} />
                                                    </div>
                                                    {topAgents.length > 0 && (
                                                        <div className="mt-2 flex flex-wrap gap-1 items-center">
                                                            <span className="text-xs text-slate-400">Agents:</span>
                                                            {topAgents.map((a, i) => (
                                                                <span key={i} className="text-xs font-medium text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">{a}</span>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>

                {/* ── Article List Section ──────────────────────────────────────── */}
                <div>

                    {/* Controls */}
                    <div className="flex flex-col md:flex-row justify-between items-center mb-6">
                        <div className="flex items-baseline gap-6 mb-4 md:mb-0">
                            <h2 className="text-2xl font-bold text-slate-800">{articles.length} Articles</h2>
                            <div className="flex gap-4 text-sm font-medium">
                                {["left", "center", "right"].map(f => {
                                    const count = articles.filter(a => (a.political_bias || a.bias || "").toLowerCase().includes(f)).length;
                                    const activeColor = f === "left" ? "text-red-600" : f === "center" ? "text-slate-500" : "text-blue-700";
                                    return (
                                        <button key={f} onClick={() => setFilter(f)}
                                            className={`capitalize ${filter === f ? `${activeColor} font-bold` : "text-slate-500 hover:text-slate-800"}`}>
                                            {f.charAt(0).toUpperCase() + f.slice(1)} ({count})
                                        </button>
                                    );
                                })}
                                {filter !== "all" && (
                                    <button onClick={() => setFilter("all")} className="text-slate-400 hover:text-slate-600 underline">Clear</button>
                                )}
                            </div>
                        </div>
                        <div className="flex items-center gap-2 w-full md:w-auto">
                            <div className="relative w-full md:w-64">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input placeholder="Search articles..." className="pl-9 bg-white"
                                    value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
                            </div>
                            <Button variant="outline" size="icon">
                                <Filter className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>

                    <div className="w-full h-px bg-slate-200 mb-8" />

                    {/* ── Comparative Coverage Analysis (LLM) ── */}
                    {(parsedComparative.left || parsedComparative.center || parsedComparative.right) && (
                        <div className="mb-8 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                            <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
                                <Sparkles className="h-4 w-4 text-indigo-500" />
                                <h3 className="font-semibold text-slate-700">Comparative Coverage Analysis</h3>
                                <span className="text-xs text-slate-400 ml-1">— AI analysis of how each side frames this story</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">
                                {[
                                    { key: "left", label: "Left Framing", headerClass: "text-red-700", dotClass: "bg-red-500", bgClass: "bg-red-50/50" },
                                    { key: "center", label: "Center Framing", headerClass: "text-slate-600", dotClass: "bg-slate-400", bgClass: "bg-slate-50/50" },
                                    { key: "right", label: "Right Framing", headerClass: "text-blue-700", dotClass: "bg-blue-500", bgClass: "bg-blue-50/50" },
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
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Article list ── */}
                    <div className="space-y-4">
                        {filteredArticles.map((article, idx) => {
                            const biasLabel = getBiasLabel(article.political_bias || article.bias);
                            return (
                                <div key={idx} className="flex gap-4 p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-slate-100 items-start">
                                    {/* Logo */}
                                    <div className="h-12 w-12 rounded-full bg-slate-100 flex-shrink-0 overflow-hidden border border-slate-200">
                                        <img
                                            src={getSourceIcon(article.source)}
                                            alt={article.source}
                                            className="h-full w-full object-cover p-2"
                                            onError={(e) => { e.target.style.display = "none"; }}
                                        />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-semibold text-lg text-slate-900 hover:text-blue-600 cursor-pointer leading-tight"
                                            onClick={() => window.open(article.url, '_blank')}>
                                            {article.title}
                                        </h3>

                                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                                            <span className="font-medium text-slate-700 text-sm">{article.source}</span>
                                            <span className="text-slate-300">•</span>
                                            <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${biasLabel.color}`}>
                                                {biasLabel.label}
                                            </span>
                                        </div>

                                        {/* Summary from CSV */}
                                        {article.summary && (
                                            <p className="text-slate-600 mt-2 text-sm line-clamp-2">{article.summary}</p>
                                        )}
                                    </div>

                                    {/* Copies URL */}
                                    <button
                                        className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded hover:bg-slate-100 transition-colors"
                                        title={copiedIdx === idx ? "Copied!" : "Copy link"}
                                        onClick={() => handleCopy(article.url, idx)}
                                    >
                                        {copiedIdx === idx
                                            ? <span className="text-green-500 text-xs font-bold">✓</span>
                                            : <Copy className="h-4 w-4 text-slate-400 hover:text-slate-600" />
                                        }
                                    </button>
                                </div>
                            );
                        })}

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
