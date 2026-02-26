
const MediaBiasChart = ({ articles, metrics }) => {
    const SG_DOMAINS = {
        "channel newsasia": "channelnewsasia.com",
        "the straits times": "straitstimes.com",
        "today online": "todayonline.com",
        "the business times": "businesstimes.com.sg",
        "mothership": "mothership.sg",
        "yahoo news singapore": "sg.yahoo.com",
    };

    const getSourceIcon = (source) => {
        const key = source?.toLowerCase().trim();
        const domain = SG_DOMAINS[key] ?? `${key?.replace(/\s+/g, '')}.com`;
        return `https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${domain}&size=32`;
    };

    return (
        <div className="bg-white rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-sm border border-slate-100 h-full">
            <h3 className="font-semibold text-slate-700 mb-6">Media Bias Chart</h3>

            <div className="w-full flex justify-between h-32 gap-2 px-2">
                {[
                    { key: "left", label: "Left", pct: metrics.left, hasData: metrics.raw.left > 0, barColor: "bg-blue-400" },
                    { key: "leaningLeft", label: "L. Left", pct: metrics.leaningLeft, hasData: metrics.raw.leaningLeft > 0, barColor: "bg-blue-200" },
                    { key: "center", label: "Center", pct: metrics.center, hasData: metrics.raw.center > 0, barColor: "bg-purple-400" },
                    { key: "leaningRight", label: "L. Right", pct: metrics.leaningRight, hasData: metrics.raw.leaningRight > 0, barColor: "bg-red-200" },
                    { key: "right", label: "Right", pct: metrics.right, hasData: metrics.raw.right > 0, barColor: "bg-red-400" },
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
                                    if (s.bias.includes("left")) pillClass = "bg-blue-100 border-blue-200 text-blue-800";
                                    else if (s.bias.includes("right")) pillClass = "bg-red-100 border-red-200 text-red-800";
                                    else if (s.bias.includes("center")) pillClass = "bg-purple-100 border-purple-200 text-purple-800";

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
    );
};

export default MediaBiasChart;
