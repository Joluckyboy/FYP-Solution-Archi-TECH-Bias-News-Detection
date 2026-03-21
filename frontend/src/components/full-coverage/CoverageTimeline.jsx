import { useMemo, useState } from 'react';
import { TrendingUp } from 'lucide-react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

const BIAS_CONFIG = [
    { key: "left", label: "Left", color: "#93C5FD", tooltipColor: "#2563EB" },         // blue-300
    { key: "leaning_left", label: "Leaning Left", color: "#BFDBFE", tooltipColor: "#3B82F6" },  // blue-200
    { key: "center", label: "Center", color: "#E9D5FF", tooltipColor: "#9333EA" },       // purple-200
    { key: "leaning_right", label: "Leaning Right", color: "#FECACA", tooltipColor: "#EF4444" }, // red-200
    { key: "right", label: "Right", color: "#FCA5A5", tooltipColor: "#DC2626" },        // red-300
];

const getBiasKey = (rawBias) => {
    const b = (rawBias || '').toLowerCase().trim();
    if (b === 'left') return 'left';
    if (b === 'right') return 'right';
    if (b === 'center') return 'center';
    if (b.includes('left')) return 'leaning_left';
    if (b.includes('right')) return 'leaning_right';
    return 'center';
};

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;
    const dateData = payload[0]?.payload;
    const rawArticles = dateData?.rawArticles || [];
    const total = dateData?.totalArticles || 0;

    const getBiasColor = (bias) => {
        const config = BIAS_CONFIG.find(c => c.key === bias);
        return config ? config.tooltipColor : '#64748B';
    };

    return (
        <div style={{
            background: '#fff',
            border: '1px solid #E2E8F0',
            borderRadius: '10px',
            padding: '12px 16px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
            maxWidth: '380px',
            fontSize: '12px',
        }}>
            <p style={{ fontWeight: 700, color: '#1E293B', marginBottom: '8px', borderBottom: '1px solid #F1F5F9', paddingBottom: '6px' }}>
                📅 {label} <span style={{ fontWeight: 400, color: '#64748B', marginLeft: '4px' }}>({total} articles)</span>
            </p>
            <div style={{ marginBottom: rawArticles.length ? '10px' : 0 }}></div>
            {rawArticles.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {rawArticles.slice(0, 5).map((a, idx) => (
                        <div key={idx}>
                            <p style={{ fontWeight: 600, color: '#334155', marginBottom: '4px', lineHeight: '1.3' }}>
                                📰 {a.title}
                            </p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                <span style={{
                                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                                    padding: '2px 6px', borderRadius: '4px',
                                    background: `${getBiasColor(a.bias)}15`,
                                    border: `1px solid ${getBiasColor(a.bias)}30`,
                                    color: getBiasColor(a.bias), fontWeight: 600, fontSize: '10px'
                                }}>
                                    {a.source}
                                    <span style={{ fontWeight: 400 }}>
                                        ({BIAS_CONFIG.find(c => c.key === a.bias)?.label || 'Unknown Bias'})
                                    </span>
                                </span>
                            </div>
                        </div>
                    ))}
                    {rawArticles.length > 5 && (
                        <p style={{ fontWeight: 600, color: '#94A3B8', fontSize: '11px', fontStyle: 'italic', marginTop: '2px' }}>
                            + {rawArticles.length - 5} more articles
                        </p>
                    )}
                </div>
            )}
        </div>
    );
};

const CoverageTimeline = ({ articles }) => {
    const [selectedSource, setSelectedSource] = useState('All');

    const sources = useMemo(() => {
        if (!articles || articles.length === 0) return [];
        const uniqueSources = new Set(articles.map(a => a.source || 'Unknown'));
        return Array.from(uniqueSources).sort();
    }, [articles]);

    const data = useMemo(() => {
        if (!articles || articles.length === 0) return [];

        const filteredArticles = selectedSource === 'All'
            ? articles
            : articles.filter(a => (a.source || 'Unknown') === selectedSource);

        const dateMap = {};
        filteredArticles.forEach(a => {
            const rawDate = a.published_at || a.published_date || a.publishedAt;
            if (!rawDate) return;
            const dateObj = new Date(rawDate);
            if (isNaN(dateObj)) return;

            const month = dateObj.toLocaleString('default', { month: 'short' });
            const day = dateObj.getDate();
            const dateKey = `${month} ${day}`;

            if (!dateMap[dateKey]) {
                dateMap[dateKey] = {
                    date: dateKey,
                    timestamp: dateObj.getTime(),
                    left: 0, leaning_left: 0, center: 0, leaning_right: 0, right: 0,
                    totalArticles: 0,
                    rawArticles: [],
                };
            }

            const biasKey = getBiasKey(a.political_bias || a.bias);
            dateMap[dateKey][biasKey] += 1;
            dateMap[dateKey].totalArticles += 1;
            dateMap[dateKey].rawArticles.push({
                title: a.title || '',
                source: a.source || 'Unknown',
                bias: biasKey,
            });
        });

        return Object.values(dateMap).sort((a, b) => a.timestamp - b.timestamp);
    }, [articles, selectedSource]);

    if (!data || data.length === 0) {
        return (
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 flex flex-col h-full w-full overflow-hidden opacity-50">
                <div className="h-1 w-full bg-slate-300" />
                <div className="px-6 py-4 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-slate-500" />
                        <h3 className="text-lg font-bold text-slate-800 tracking-tight">Coverage Timeline</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-3">Article volume per day, broken down by political bias</p>
                </div>
                <div className="flex-1 flex items-center justify-center min-h-[300px] text-sm text-slate-400">
                    Not enough timeline data available
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 flex flex-col h-full w-full overflow-visible">
            <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-slate-500" />
                        <h3 className="text-lg font-bold text-slate-800 tracking-tight">Coverage Timeline</h3>
                    </div>
                    <p className="text-sm text-slate-500 mt-1">Article volume per day</p>
                </div>
                {sources && sources.length > 0 && (
                    <div className="flex items-center gap-2">
                        <label htmlFor="source-filter" className="text-sm font-medium text-slate-600">
                            Outlet:
                        </label>
                        <select
                            id="source-filter"
                            className="bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 outline-none cursor-pointer min-w-[140px]"
                            value={selectedSource}
                            onChange={(e) => setSelectedSource(e.target.value)}
                        >
                            <option value="All">All Outlets</option>
                            {sources.map(source => (
                                <option key={source} value={source}>{source}</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>
            <div className="flex-1 w-full min-h-[320px] p-6">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 5, right: 30, left: 10, bottom: 50 }} barCategoryGap="20%">
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                        <XAxis
                            dataKey="date"
                            tick={{ fontSize: 12, fill: '#64748B' }}
                            tickLine={false}
                            axisLine={{ stroke: '#CBD5E1' }}
                            label={{ value: 'Date of Publish', position: 'insideBottom', offset: -16, fontSize: 11, fill: '#94A3B8', fontStyle: 'italic' }}
                        />
                        <YAxis
                            tick={{ fontSize: 12, fill: '#64748B' }}
                            tickLine={false}
                            axisLine={false}
                            allowDecimals={false}
                            label={{ value: 'No. of Articles', angle: -90, position: 'insideLeft', offset: 10, fontSize: 11, fill: '#94A3B8', fontStyle: 'italic' }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(148,163,184,0.08)' }} allowEscapeViewBox={{ x: true, y: true }} wrapperStyle={{ zIndex: 50 }} />
                        <Bar
                            dataKey="totalArticles"
                            name="Articles"
                            fill="#3B82F6"
                            radius={[4, 4, 0, 0]}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default CoverageTimeline;
