import { useState } from 'react';
import { Search, Filter, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import ArticleCard from './ArticleCard';

const ArticleListSection = ({ articles, topic, enrichmentLoading, copiedIdx, handleCopy }) => {
    const [filter, setFilter] = useState("all");
    const [searchQuery, setSearchQuery] = useState("");

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

    return (
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

            {/* Comparative Coverage Analysis (LLM) */}
            {(enrichmentLoading || parsedComparative.left || parsedComparative.center || parsedComparative.right) && (
                <div className="mb-8 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-indigo-500" />
                        <h3 className="font-semibold text-slate-700">Comparative Coverage Analysis</h3>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400 ml-1">— AI analysis of how each side frames this story</span>
                            {enrichmentLoading && <Skeleton className="h-4 w-20 inline-block" />}
                        </div>
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
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Article list */}
            <div className="space-y-4">
                {filteredArticles.map((article, idx) => (
                    <ArticleCard
                        key={idx}
                        article={article}
                        idx={idx}
                        copiedIdx={copiedIdx}
                        handleCopy={handleCopy}
                    />
                ))}

                {filteredArticles.length === 0 && (
                    <div className="text-center py-12 text-slate-500">
                        No articles found matching your criteria.
                    </div>
                )}
            </div>
        </div>
    );
};

export default ArticleListSection;
