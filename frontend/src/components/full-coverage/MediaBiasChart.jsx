
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

            {(() => {
                const bars = [
                    { key: "left",      label: "Left",        pct: metrics.left,        count: metrics.raw.left,         barColor: "bg-blue-500" },
                    { key: "leanLeft",  label: "Leaning Left",pct: metrics.leaningLeft, count: metrics.raw.leaningLeft,  barColor: "bg-blue-300" },
                    { key: "center",    label: "Center",      pct: metrics.center,      count: metrics.raw.center,       barColor: "bg-purple-400" },
                    { key: "leanRight", label: "Leaning Right",pct: metrics.leaningRight,count: metrics.raw.leaningRight,barColor: "bg-red-300" },
                    { key: "right",     label: "Right",       pct: metrics.right,       count: metrics.raw.right,        barColor: "bg-red-500" },
                ];
                return (
                    <div className="w-full px-2">
                        {/* Row 1: count labels — all same height so they don't affect bar alignment */}
                        <div className="flex justify-between gap-2 mb-1">
                            {bars.map(({ key, count }) => (
                                <div key={key} className="flex-1 flex justify-center">
                                    <span className="text-xs font-semibold text-slate-500">{count}</span>
                                </div>
                            ))}
                        </div>
                        {/* Row 2: fixed-height bar area — all bars grow from the same baseline */}
                        <div className="flex justify-between gap-2 h-28 items-end">
                            {bars.map(({ key, label, pct, count, barColor }) => (
                                <div
                                    key={key}
                                    className={`flex-1 rounded-t-md transition-all duration-500 ${count > 0 ? barColor : "bg-gray-100"}`}
                                    style={{ height: `${Math.max(count > 0 ? 6 : 0, pct)}%` }}
                                    title={`${label}: ${count} article${count === 1 ? '' : 's'}`}
                                />
                            ))}
                        </div>
                        {/* Row 3: baseline rule */}
                        <div className="w-full border-t-2 border-slate-200" />
                        {/* Row 4: axis labels — all same height */}
                        <div className="flex justify-between gap-2 mt-1.5">
                            {bars.map(({ key, label }) => (
                                <div key={key} className="flex-1 flex justify-center">
                                    <span className="text-[10px] uppercase font-bold text-slate-400 text-center leading-tight">{label}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })()}

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
