import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import get_api from "@/config/config";
import axios from "axios";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from "recharts"; 

const HowItWorksPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const load = async () => {
      try {
        const api = await get_api();
        const res = await axios.get(`${api}/application/scraper_stats`);
        setStats(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="flex justify-center p-20">Loading scraper stats...</div>;

  // Transform trend data for chart
  const trendData = stats?.dailyTrend?.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-SG', { month: 'short', day: 'numeric' }),
    count: item.count
  })) || [];

  return (
    <div className="max-w-6xl mx-auto p-8 space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          How Our News Scraper Works
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Our web scraper is like a friendly robot that automatically visits news websites every day! We then collect and analyse them for bias by comparing word choices, sources cited, and tones in articles etc. 
        </p>
      </div>

      {/* Live Stats KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-green-600">
              {stats?.coreStats?.todayArticles || 0}
            </CardTitle>
            <p>New articles today</p>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-blue-600">
              {stats?.coreStats?.cumulativeTotal?.toLocaleString() || 0}
            </CardTitle>
            <p>Total articles collected</p>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-purple-600">
              {stats?.coreStats?.avgDaily || 0}
            </CardTitle>
            <p>Average articles per day</p>
          </CardHeader>
        </Card>
      </div>

      {/* Sources & Countries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>News Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">Top sources:</p>
            {Object.entries(stats?.sourceBreakdown || {}).slice(0, 3).map(([source, count]) => (  // ← Removed unused 'i'
              <div key={source} className="flex items-center justify-between py-2 border-b last:border-b-0">
                <span className="font-medium">{source}</span>
                <span className="text-2xl font-bold text-blue-600">{count}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Countries Covered</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">Geographic coverage:</p>
            {Object.entries(stats?.countriesDistribution || {}).slice(0, 5).map(([country, count]) => (
              <div key={country} className="flex items-center justify-between py-2 border-b last:border-b-0">
                <span className="font-medium">{country}</span>
                <span className="font-bold text-green-600">{count} articles</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Recent Collection Trend */}
      {trendData.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Articles Collected — Last 14 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={trendData}>
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Simple Process Explanation */}
      <Card>
        <CardHeader>
          <CardTitle>The Process</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div>
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📰</span>
            </div>
            <h3 className="font-semibold mb-2">1. Collect</h3>
            <p className="text-sm text-muted-foreground">Daily robot visits to news websites, saves international news to our database</p>
          </div>
          <div>
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🔍</span>
            </div>
            <h3 className="font-semibold mb-2">2. Analyse</h3>
            <p className="text-sm text-muted-foreground">AI models and rule-based checks look out for bias indicators in every article.</p>
          </div>
          <div>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="font-semibold mb-2">3. Show Truth</h3>
            <p className="text-sm text-muted-foreground">Our dashbboard then displays patterns across thousands of articles!</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HowItWorksPage;
