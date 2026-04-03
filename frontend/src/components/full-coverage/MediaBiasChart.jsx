import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";
import { normalizeBias, getBiasLabel } from "@/utils/biasNormalizer";

const BIAS_CONFIG = [
    { key: "left", label: "Left", color: "#93C5FD" },         // blue-300
    { key: "leaningLeft", label: "Lean Left", color: "#BFDBFE" },  // blue-200
    { key: "center", label: "Center", color: "#E9D5FF" },       // purple-200
    { key: "leaningRight", label: "Lean Right", color: "#FECACA" }, // red-200
    { key: "right", label: "Right", color: "#FCA5A5" },        // red-300
];

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
    const domain = SG_DOMAINS[key] ?? `${key?.replace(/\s+/g, "")}.com`;
    return `https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${domain}&size=32`;
};

// Custom label inside slice – only show if slice is big enough
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.05) return null;
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    return (
        <text x={x} y={y} fill="#000" textAnchor="middle" dominantBaseline="central"
            style={{ fontSize: 11, fontWeight: 700 }}>
            {`${(percent * 100).toFixed(0)}%`}
        </text>
    );
};

const MediaBiasChart = ({ articles, metrics }) => {
    const totalArticles = metrics.total || 0;

    const chartData = BIAS_CONFIG
        .map(({ key, label, color }) => ({
            name: label,
            value: metrics.raw[key] || 0,
            color,
        }))
        .filter(d => d.value > 0);

    return (
        <div className="bg-white rounded-xl p-5 flex flex-col shadow-sm border border-slate-100 h-full">
            <h3 className="font-semibold text-lg text-slate-700 mb-1 text-center">News Article Bias Analysis</h3>
            <p className="text-base text-slate-500 mb-2 text-center">
                This chart shows the political bias distribution of{" "}
                <span className="font-bold text-slate-700">{totalArticles}</span>{" "}
                article{totalArticles !== 1 ? "s" : ""} covered by this news cluster.
            </p>

            {/* Pie Chart */}
            <div className="w-full h-48 flex-shrink-0 mt-2 mb-1">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="45%"
                            outerRadius={75}
                            dataKey="value"
                            labelLine={false}
                            label={renderCustomLabel}
                        >
                            {chartData.map((entry, i) => (
                                <Cell key={i} fill={entry.color} stroke="#fff" strokeWidth={2} />
                            ))}
                        </Pie>
                        <Tooltip
                            content={({ active, payload }) => {
                                if (!active || !payload?.length) return null;
                                const { name, value } = payload[0].payload;
                                const pct = totalArticles ? ((value / totalArticles) * 100).toFixed(1) : 0;
                                return (
                                    <div style={{
                                        background: "#fff",
                                        border: "1px solid #E2E8F0",
                                        borderRadius: "8px",
                                        padding: "8px 12px",
                                        fontSize: "13px",
                                        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                                    }}>
                                        <p style={{ fontWeight: 700, color: "#1E293B", marginBottom: 2 }}>{name}</p>
                                        <p style={{ color: "#64748B" }}>
                                            {value} article{value !== 1 ? "s" : ""} ({pct}%)
                                        </p>
                                    </div>
                                );
                            }}
                        />
                        <Legend
                            iconType="circle"
                            iconSize={10}
                            wrapperStyle={{ fontSize: "14px", paddingTop: "8px" }}
                            formatter={(value) => <span style={{ color: "#000000", fontWeight: 500 }}>{value}</span>}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Polarisation Analysis */}
            <div className="mt-2 pt-3 border-t border-slate-100 w-full">
                <h4 className="font-semibold text-lg text-slate-700 mb-1 text-center">
                    Polarisation Analysis
                </h4>
                {(() => {
                    const uniqueSources = {};
                    articles.forEach(a => {
                        if (a.source && !uniqueSources[a.source]) {
                            uniqueSources[a.source] = {
                                source: a.source,
                                bias: (a.political_bias || a.bias || "").toLowerCase(),
                            };
                        }
                    });

                    const BIAS_RANK = {
                        "left": 0,
                        "lean-left": 1,
                        "center": 2,
                        "lean-right": 3,
                        "right": 4,
                    };
                    const getBiasRank = (bias) => {
                        return BIAS_RANK[normalizeBias(bias)] ?? 2; // default to center
                    };

                    const sources = Object.values(uniqueSources).sort(
                        (a, b) => getBiasRank(a.bias) - getBiasRank(b.bias)
                    );
                    return (
                        <div className="flex flex-col items-center">
                            <p className="text-base text-slate-500 mb-2">
                                This story is covered by{" "}
                                <span className="font-bold text-slate-800">{sources.length}</span> unique sources.
                            </p>
                            <div className="flex flex-wrap justify-center gap-2">
                                {sources.map((s, i) => {
                                    let pillClass = "bg-slate-100 border-slate-200 text-slate-700";
                                    const normalized = normalizeBias(s.bias);
                                    if (normalized === "lean-left")  pillClass = "bg-blue-100 border-blue-200 text-blue-600";
                                    else if (normalized === "left")  pillClass = "bg-blue-200 border-blue-300 text-blue-800";
                                    else if (normalized === "lean-right") pillClass = "bg-red-100 border-red-200 text-red-600";
                                    else if (normalized === "right") pillClass = "bg-red-200 border-red-300 text-red-800";
                                    else if (normalized === "center") pillClass = "bg-purple-100 border-purple-200 text-purple-800";
                                    return (
                                        <div key={i}
                                            className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-sm font-medium ${pillClass}`}
                                            title={`${s.source} (${getBiasLabel(s.bias)})`}>
                                            <img
                                                src={getSourceIcon(s.source)}
                                                alt={s.source}
                                                className="h-4 w-4 rounded-full object-cover flex-shrink-0"
                                                onError={(e) => { e.target.style.display = "none"; }}
                                            />
                                            <span className="max-w-[100px] truncate">{s.source}</span>
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
