import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Newspaper, Sparkles } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const FeaturedCoverageGrid = ({ featuredLeft, featuredCenter, featuredRight, parsedComparative, enrichmentLoading }) => {
    const hasComparative = enrichmentLoading || parsedComparative?.left || parsedComparative?.center || parsedComparative?.right;

    return (
        <Card className="mb-12 shadow-sm border border-slate-200 overflow-hidden w-full">
            <CardHeader className="pb-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                    <Newspaper className="h-5 w-5 text-slate-500" />
                    <CardTitle className="text-2xl font-bold text-slate-800">Featured Coverage of Story</CardTitle>
                </div>
                <p className="text-base text-slate-500 mb-3">Latest representative articles from each political perspective</p>
            </CardHeader>

            <CardContent className="p-4 space-y-6">

                {/* ── 1. Featured article cards (top) ────────────── */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                        { label: "Left", article: featuredLeft, cardClass: "bg-blue-200 border-blue-300", hoverColor: "group-hover:text-blue-700", dividerColor: "border-blue-200/50", emptyMsg: "No left-leaning coverage found." },
                        { label: "Center", article: featuredCenter, cardClass: "bg-purple-100 border-purple-200", hoverColor: "group-hover:text-purple-700", dividerColor: "border-purple-100", emptyMsg: "No center coverage found." },
                        { label: "Right", article: featuredRight, cardClass: "bg-red-200 border-red-300", hoverColor: "group-hover:text-red-700", dividerColor: "border-red-200/50", emptyMsg: "No right-leaning coverage found." },
                    ].map(({ label, article, cardClass, hoverColor, dividerColor, emptyMsg }) => (
                        <div key={label} className="flex flex-col">
                            <h3 className="text-center text-base font-semibold text-slate-400 uppercase tracking-wide mb-1.5">{label}</h3>
                            <Card
                                className={`${cardClass} shadow-sm hover:shadow-md transition-shadow cursor-pointer group h-full flex flex-col`}
                                onClick={() => article && window.open(article.url, '_blank')}
                            >
                                <CardContent className="p-3 flex flex-col h-full">
                                    {article ? (
                                        <>
                                            <h4 className={`text-base font-semibold text-slate-900 mb-2 ${hoverColor} leading-snug`}>
                                                {article.title}
                                            </h4>
                                            {article.summary && (
                                                <p className="text-sm text-slate-600 line-clamp-2 mb-2">{article.summary}</p>
                                            )}
                                            <div className={`mt-auto pt-2 border-t ${dividerColor} flex items-center justify-between`}>
                                                <p className="font-medium text-slate-700 text-sm">{article.source}</p>
                                                {article.published_at && (
                                                    <span className="text-sm text-slate-400">{String(article.published_at).slice(0, 10)}</span>
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

                {/* ── 2. Comparative Coverage Analysis (below) ───────── */}
                {hasComparative && (
                    <div className="rounded-xl border border-slate-200 overflow-hidden">
                        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
                            <div className="flex items-center gap-2 flex-wrap">
                                <Sparkles className="h-4 w-4 text-indigo-500" />
                                <h3 className="text-lg font-bold text-slate-800 tracking-tight">Comparative Coverage Analysis</h3>
                                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 text-sm font-medium text-indigo-600">
                                    <Sparkles className="h-3 w-3" /> AI Generated
                                </span>
                                {enrichmentLoading && <Skeleton className="h-4 w-20 inline-block" />}
                            </div>
                            <p className="text-base text-slate-500 mt-1">
                                Explore how differently the Left, Center and Right would cover the same piece of news.
                            </p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100">
                            {enrichmentLoading && !parsedComparative?.left && !parsedComparative?.center && !parsedComparative?.right ? (
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
                                    { key: "left", label: "Left Framing", headerClass: "text-blue-700", dotClass: "bg-blue-500", bgClass: "bg-blue-200" },
                                    { key: "center", label: "Center Framing", headerClass: "text-purple-600", dotClass: "bg-purple-400", bgClass: "bg-purple-100" },
                                    { key: "right", label: "Right Framing", headerClass: "text-red-700", dotClass: "bg-red-500", bgClass: "bg-red-200" },
                                ].map(({ key, label, headerClass, dotClass, bgClass }) => (
                                    <div key={key} className={`p-5 ${bgClass}`}>
                                        <div className="flex items-center gap-2 mb-3">
                                            <div className={`h-2 w-2 rounded-full ${dotClass}`} />
                                            <p className={`text-sm font-bold uppercase tracking-wider ${headerClass}`}>{label}</p>
                                        </div>
                                        <p className="text-base text-slate-700 leading-relaxed">
                                            {parsedComparative?.[key] || <span className="text-slate-400 italic">No data available</span>}
                                        </p>
                                    </div>
                                ))
                            )}
                        </div>
                        <p className="px-6 py-3 text-sm text-slate-400 italic border-t border-slate-100 bg-white">
                            ✦ This analysis was generated by AI and may not fully represent each outlet's editorial stance.
                        </p>
                    </div>
                )}

            </CardContent>
        </Card>
    );
};

export default FeaturedCoverageGrid;
