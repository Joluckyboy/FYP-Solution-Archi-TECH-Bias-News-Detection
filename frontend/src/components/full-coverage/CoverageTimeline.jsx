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

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    // Find the dateMap entry for this label to get article details
    const articlesForDate = payload[0]?.payload?.articlesByBias || {};

    return (
        <div style={{
            background: '#fff',
            border: '1px solid #E2E8F0',
            borderRadius: '10px',
            padding: '12px 16px',
            boxShadow: '0 4px 16px rgb(0 0 0 / 0.12)',
            maxWidth: '320px',
            fontSize: '12px',
        }}>
            <p style={{ fontWeight: 700, color: '#1E293B', marginBottom: '8px', borderBottom: '1px solid #F1F5F9', paddingBottom: '6px' }}>
                📅 {label}
            </p>
            {BIAS_CONFIG.map(({ key, label: biasLabel, color }) => {
                const arts = articlesForDate[key];
                if (!arts || arts.length === 0) return null;
                return (
                    <div key={key} style={{ marginBottom: '8px' }}>
                        <p style={{ color, fontWeight: 700, marginBottom: '3px' }}>
                            {biasLabel} ({arts.length} article{arts.length > 1 ? 's' : ''})
                        </p>
                        {arts.slice(0, 3).map((a, i) => (
                            <p key={i} style={{ color: '#475569', marginLeft: '8px', marginBottom: '2px', lineHeight: '1.4' }}>
                                • <span style={{ fontWeight: 600 }}>{a.source}</span>
                                {a.title ? `: ${a.title.length > 60 ? a.title.slice(0, 60) + '…' : a.title}` : ''}
                            </p>
                        ))}
                        {arts.length > 3 && (
                            <p style={{ color: '#94A3B8', marginLeft: '8px', fontStyle: 'italic' }}>
                                +{arts.length - 3} more
                            </p>
                        )}
                    </div>
                );
            })}
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
                    articlesByBias: { left: [], leaning_left: [], center: [], leaning_right: [], right: [] },
                };
            }

            const biasKey = getBiasKey(a.political_bias || a.bias);
            dateMap[dateKey][biasKey] += 1;
            dateMap[dateKey].articlesByBias[biasKey].push({
                title: a.title || '',
                source: a.source || 'Unknown',
            });
        });

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
