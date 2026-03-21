import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Newspaper } from "lucide-react";

const FeaturedCoverageGrid = ({ featuredLeft, featuredCenter, featuredRight }) => {
    return (
        <Card className="mb-12 shadow-sm border border-slate-200 overflow-hidden">
            <CardHeader className="pb-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                    <Newspaper className="h-5 w-5 text-slate-500" />
                    <CardTitle className="text-xl font-bold text-slate-800">Featured Coverage of Story</CardTitle>
                </div>
                <p className="text-sm text-slate-500 mb-3">Latest representative articles from each political perspective</p>
            </CardHeader>

            <CardContent className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                        { label: "Left", article: featuredLeft, cardClass: "bg-blue-200 border-blue-300", hoverColor: "group-hover:text-blue-700", dividerColor: "border-blue-200/50", emptyMsg: "No left-leaning coverage found." },
                        { label: "Center", article: featuredCenter, cardClass: "bg-purple-100 border-purple-200", hoverColor: "group-hover:text-purple-700", dividerColor: "border-purple-100", emptyMsg: "No center coverage found." },
                        { label: "Right", article: featuredRight, cardClass: "bg-red-200 border-red-300", hoverColor: "group-hover:text-red-700", dividerColor: "border-red-200/50", emptyMsg: "No right-leaning coverage found." },
                    ].map(({ label, article, cardClass, hoverColor, dividerColor, emptyMsg }) => (
                        <div key={label} className="flex flex-col">
                            <h3 className="text-center text-sm font-semibold text-slate-400 uppercase tracking-wide mb-1.5">{label}</h3>
                            <Card
                                className={`${cardClass} shadow-sm hover:shadow-md transition-shadow cursor-pointer group h-full flex flex-col`}
                                onClick={() => article && window.open(article.url, '_blank')}
                            >
                                <CardContent className="p-3 flex flex-col h-full">
                                    {article ? (
                                        <>
                                            <h4 className={`text-sm font-semibold text-slate-900 mb-2 ${hoverColor} leading-snug`}>
                                                {article.title}
                                            </h4>
                                            {article.summary && (
                                                <p className="text-xs text-slate-600 line-clamp-2 mb-2">{article.summary}</p>
                                            )}
                                            <div className={`mt-auto pt-2 border-t ${dividerColor} flex items-center justify-between`}>
                                                <p className="font-medium text-slate-700 text-xs">{article.source}</p>
                                                {article.published_at && (
                                                    <span className="text-xs text-slate-400">{String(article.published_at).slice(0, 10)}</span>
                                                )}
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-slate-500 italic text-xs">{emptyMsg}</div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
};

export default FeaturedCoverageGrid;
