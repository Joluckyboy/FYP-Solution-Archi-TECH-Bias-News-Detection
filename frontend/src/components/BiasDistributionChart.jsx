import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const BIAS_COLORS = {
    'left': '#3b82f6',        // Blue-500
    'leaning-left': '#60a5fa', // Blue-400
    'center': '#9ca3af',      // Gray-400
    'leaning-right': '#f87171',// Red-400
    'right': '#ef4444',       // Red-500
    'unknown': '#e5e7eb'      // Gray-200
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-background border rounded-lg p-3 shadow-lg text-sm">
                <p className="font-semibold mb-2">{label}</p>
                {payload.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2 mb-1">
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                        />
                        <span className="capitalize">{entry.name.replace('-', ' ')}:</span>
                        <span className="font-mono">{entry.value}</span>
                    </div>
                ))}
                <div className="mt-2 pt-2 border-t font-semibold flex justify-between">
                    <span>Total:</span>
                    <span>{payload.reduce((sum, entry) => sum + entry.value, 0)}</span>
                </div>
            </div>
        );
    }
    return null;
};

const BiasDistributionChart = ({ data, loading }) => {
    if (loading) {
        return (
            <Card className="col-span-4">
                <CardHeader>
                    <CardTitle>Bias Distribution by News Outlet</CardTitle>
                    <CardDescription>Political bias breakdown for top news sources</CardDescription>
                </CardHeader>
                <CardContent className="h-[400px] flex items-center justify-center">
                    <p className="text-muted-foreground">Loading chart data...</p>
                </CardContent>
            </Card>
        );
    }

    if (!data || data.length === 0) {
        return (
            <Card className="col-span-4">
                <CardContent className="h-[400px] flex items-center justify-center">
                    <p className="text-muted-foreground">No data available for chart</p>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="col-span-4">
            <CardHeader>
                <CardTitle>Bias Distribution by News Outlet</CardTitle>
                <CardDescription>Top sources by article volume and their political bias composition</CardDescription>
            </CardHeader>
            <CardContent className="pl-0">
                <div className="h-[400px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                            data={data}
                            margin={{
                                top: 20,
                                right: 30,
                                left: 20,
                                bottom: 60,
                            }}
                        >
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis
                                dataKey="name"
                                angle={-45}
                                textAnchor="end"
                                height={80}
                                interval={0}
                                tick={{ fontSize: 12 }}
                            />
                            <YAxis />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend verticalAlign="top" height={36} />

                            <Bar dataKey="left" stackId="a" fill={BIAS_COLORS['left']} name="Left" />
                            <Bar dataKey="leaning-left" stackId="a" fill={BIAS_COLORS['leaning-left']} name="Leaning Left" />
                            <Bar dataKey="center" stackId="a" fill={BIAS_COLORS['center']} name="Center" />
                            <Bar dataKey="leaning-right" stackId="a" fill={BIAS_COLORS['leaning-right']} name="Leaning Right" />
                            <Bar dataKey="right" stackId="a" fill={BIAS_COLORS['right']} name="Right" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
};

export default BiasDistributionChart;
