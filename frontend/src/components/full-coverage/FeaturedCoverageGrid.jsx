import { Card, CardContent } from "@/components/ui/card";

const FeaturedCoverageGrid = ({ featuredLeft, featuredCenter, featuredRight }) => {
    return (
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
        </div>
    );
};

export default FeaturedCoverageGrid;
