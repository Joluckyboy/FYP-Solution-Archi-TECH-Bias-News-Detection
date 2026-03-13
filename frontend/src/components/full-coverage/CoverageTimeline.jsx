import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const BIAS_CONFIG = [
    { key: 'left',         label: 'Left',          color: '#2563EB' },
    { key: 'leaning_left', label: 'Leaning Left',  color: '#60A5FA' },
    { key: 'center',       label: 'Center',        color: '#7C3AED' },
    { key: 'leaning_right',label: 'Leaning Right', color: '#F87171' },
    { key: 'right',        label: 'Right',         color: '#DC2626' },
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

// --- Clustering Helpers ---
const STOP_WORDS = new Set([
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "from", 
    "as", "is", "are", "was", "were", "be", "been", "this", "that", "these", "those", "it", "its", "has", "have"
]);

const tokenize = (text) => {
    if (!text) return new Set();
    const words = text.toLowerCase().replace(/[^\w\s]/g, '').split(/\s+/);
    return new Set(words.filter(w => w.length > 2 && !STOP_WORDS.has(w)));
};

const getJaccardSimilarity = (setA, setB) => {
    const intersection = new Set([...setA].filter(x => setB.has(x)));
    const union = new Set([...setA, ...setB]);
    return intersection.size / (union.size || 1);
};

const groupArticlesIntoEvents = (articles, similarityThreshold = 0.25) => {
    const events = []; // { title: string, tokens: Set, articles: [] }

    articles.forEach(article => {
        const title = article.title || "";
        const tokens = tokenize(title);
        
        if (tokens.size === 0) return;

        let bestMatch = null;
        let highestSim = 0;

        for (const event of events) {
            const sim = getJaccardSimilarity(tokens, event.tokens);
            if (sim > highestSim) {
                highestSim = sim;
                bestMatch = event;
            }
        }

        if (bestMatch && highestSim >= similarityThreshold) {
            bestMatch.articles.push(article);
            // Optionally, we could merge tokens, but keeping the original representation is often safer.
        } else {
            events.push({
                title: title,
                tokens: tokens,
                articles: [article],
            });
        }
    });

    // Sort events by number of covering sources (descending)
    return events.sort((a, b) => b.articles.length - a.articles.length);
};

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    // Retrieve the pre-grouped events for this specific date
    const dateData = payload[0]?.payload;
    const events = dateData?.events || [];

    const getBiasColor = (bias) => {
        const config = BIAS_CONFIG.find(c => c.key === bias);
        return config ? config.color : '#94A3B8';
    };

    return (
        <div style={{
            background: '#fff',
            border: '1px solid #E2E8F0',
            borderRadius: '10px',
            padding: '12px 16px',
            boxShadow: '0 4px 16px rgb(0 0 0 / 0.12)',
            maxWidth: '380px',
            fontSize: '12px',
        }}>
            <p style={{ fontWeight: 700, color: '#1E293B', marginBottom: '8px', borderBottom: '1px solid #F1F5F9', paddingBottom: '6px' }}>
                📅 {label} <span style={{ fontWeight: 400, color: '#64748B', marginLeft: '4px' }}>({dateData.totalArticles || 0} articles)</span>
            </p>

            {events.length === 0 ? (
                <p style={{ color: '#64748B', fontStyle: 'italic' }}>No prominent events found.</p>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {events.map((evt, idx) => (
                        <div key={idx}>
                            <p style={{ fontWeight: 700, color: '#334155', marginBottom: '4px', lineHeight: '1.3' }}>
                                📌 {evt.title}
                            </p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                {evt.articles.map((a, i) => (
                                    <span key={i} style={{
                                        display: 'inline-block',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                        background: `${getBiasColor(a.bias)}15`,
                                        border: `1px solid ${getBiasColor(a.bias)}30`,
                                        color: getBiasColor(a.bias),
                                        fontWeight: 600,
                                        fontSize: '10px'
                                    }}>
                                        {a.source}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const CoverageTimeline = ({ articles }) => {
    const data = useMemo(() => {
        if (!articles || articles.length === 0) return [];

        const dateMap = {};

        articles.forEach(a => {
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
                    left: 0,
                    leaning_left: 0,
                    center: 0,
                    leaning_right: 0,
                    right: 0,
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
                rawBias: a.political_bias || a.bias || '',
            });
        });

        // Convert the date map to an array and group raw articles into events
        return Object.values(dateMap).map(day => {
            const events = groupArticlesIntoEvents(day.rawArticles);
            // Optionally clear rawArticles to save memory if needed
            return {
                ...day,
                events,
            };
        }).sort((a, b) => a.timestamp - b.timestamp);

        return Object.values(dateMap).sort((a, b) => a.timestamp - b.timestamp);
    }, [articles]);

    if (!data || data.length === 0) {
        return (
            <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 flex flex-col h-full w-full opacity-50">
                <h3 className="font-semibold text-slate-700 mb-6 text-center">Coverage Timeline</h3>
                <div className="flex-1 flex items-center justify-center min-h-[300px] text-sm text-slate-400">
                    Not enough timeline data available
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 flex flex-col h-full w-full">
            <h3 className="font-semibold text-slate-700 mb-6 text-center">Coverage Timeline</h3>
            <div className="flex-1 w-full min-h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                        <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748B' }} tickLine={false} axisLine={{ stroke: '#CBD5E1' }} />
                        <YAxis tick={{ fontSize: 12, fill: '#64748B' }} tickLine={false} axisLine={false} allowDecimals={false} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '12px' }} />
                        {BIAS_CONFIG.map(({ key, label, color }) => (
                            <Line
                                key={key}
                                type="monotone"
                                dataKey={key}
                                name={label}
                                stroke={color}
                                strokeWidth={2.5}
                                dot={{ r: 4, strokeWidth: 2, fill: '#fff', stroke: color }}
                                activeDot={{ r: 6 }}
                                connectNulls
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default CoverageTimeline;
