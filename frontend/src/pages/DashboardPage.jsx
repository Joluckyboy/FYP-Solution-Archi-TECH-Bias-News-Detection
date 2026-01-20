import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LayoutDashboard, Newspaper, Globe, Scale, BarChart3 } from 'lucide-react';
import KPICard from '../components/KPICard';
import BiasDistributionChart from '../components/BiasDistributionChart';

const DashboardPage = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);
    const [apiUrl, setApiUrl] = useState(null);

    useEffect(() => {
        // Scraper service is running on port 8015
        setApiUrl("http://127.0.0.1:8015");
    }, []);

    useEffect(() => {
        if (!apiUrl) return;

        const fetchData = async () => {
            try {
                setLoading(true);
                // The endpoint is /scraper/dashboard/analytics based on app.py namespace
                const response = await axios.get(`${apiUrl}/scraper/dashboard/analytics`);
                setData(response.data);
                setError(null);
            } catch (err) {
                console.error("Dashboard data fetch error:", err);
                setError("Failed to load dashboard analytics. Please try again later.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [apiUrl]);

    const getDominantBias = () => {
        if (!data?.kpi?.bias_distribution) return "N/A";
        const sorted = [...data.kpi.bias_distribution].sort((a, b) => b.value - a.value);
        return sorted[0]?.name || "N/A";
    };

    return (
        <div className="container mx-auto p-6 space-y-8">
            <div className="flex flex-col space-y-2">
                <h1 className="text-3xl font-bold tracking-tight">Bias Detection Dashboard</h1>
                <p className="text-muted-foreground">
                    Overview of news bias analytics from the Kaggle dataset.
                </p>
            </div>

            {error && (
                <div className="bg-destructive/15 text-destructive p-4 rounded-md">
                    {error}
                </div>
            )}

            {/* KPI Section */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <KPICard
                    title="Total Articles"
                    value={data?.kpi?.total_articles?.toLocaleString()}
                    icon={<Newspaper />}
                    loading={loading}
                    description="Total analyzed articles in dataset"
                />
                <KPICard
                    title="News Outlets"
                    value={data?.kpi?.total_outlets}
                    icon={<LayoutDashboard />}
                    loading={loading}
                    description="Unique news sources tracked"
                />
                <KPICard
                    title="Countries"
                    value={data?.kpi?.total_countries}
                    icon={<Globe />}
                    loading={loading}
                    description="Countries represented"
                />
                <KPICard
                    title="Dominant Bias"
                    value={loading ? "..." : (getDominantBias().replace('-', ' ').toUpperCase())}
                    icon={<Scale />}
                    loading={loading}
                    description="Most common political leaning"
                />
            </div>

            {/* Charts Section */}
            <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-4">
                <BiasDistributionChart data={data?.chart_data} loading={loading} />
            </div>
        </div>
    );
};

export default DashboardPage;
