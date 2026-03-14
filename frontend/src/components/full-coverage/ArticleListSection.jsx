import { useState } from 'react';
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ArticleCard from './ArticleCard';
import FramingAnalysisPanel from './FramingAnalysisPanel';

const ArticleListSection = ({ articles, copiedIdx, handleCopy, framingDiff = {}, linguisticFraming = {} }) => {
    const [filter, setFilter] = useState("all");
    const [searchQuery, setSearchQuery] = useState("");
    const [showCount, setShowCount] = useState(5);

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

    return (
        <div>
            {/* Controls */}
            <div className="flex flex-col md:flex-row justify-between items-center mb-6">
                <div className="flex items-baseline gap-6 mb-4 md:mb-0">
                    <h2 className="text-2xl font-bold text-slate-800">{articles.length} Articles</h2>
                    <div className="flex gap-4 text-sm font-medium">
                        {["left", "center", "right"].map(f => {
                            const count = articles.filter(a => (a.political_bias || a.bias || "").toLowerCase().includes(f)).length;
                            const activeColor = f === "left" ? "text-blue-600" : f === "center" ? "text-purple-500" : "text-red-700";
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
                </div>
            </div>

            <div className="w-full h-px bg-slate-200 mb-8" />

            {/* Framing Differences in Headline */}
            <FramingAnalysisPanel
                framingDiff={framingDiff}
                linguisticFraming={linguisticFraming}
            />

            {/* Article list */}
            <div className="space-y-4">
                {filteredArticles.slice(0, showCount).map((article, idx) => (
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

                {filteredArticles.length > showCount && (
                    <div className="pt-4 flex justify-center">
                        <Button
                            variant="outline"
                            className="bg-white border-2 border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 w-full md:w-auto px-8 py-2 rounded-full font-medium transition-colors shadow-sm"
                            onClick={() => setShowCount(prev => prev + 10)}
                        >
                            Show More Articles ({filteredArticles.length - showCount} remaining)
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ArticleListSection;
