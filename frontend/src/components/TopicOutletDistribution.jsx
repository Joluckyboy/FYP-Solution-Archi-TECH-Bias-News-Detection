import React, { useEffect, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import get_api from "@/config/config";
import axios from "axios";

export default function TopicOutletDistribution() {
  const [data, setData] = useState({});
  const [selectedTopic, setSelectedTopic] = useState("general-news");
  const [loading, setLoading] = useState(true);

  // Format topic names: "general-news" → "General News"
  const formatTopic = (topic) => 
    topic
      .replace(/-/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const api = await get_api();
        const res = await axios.get(`${api}/application/visualisations`);
        setData(res.data.topicOutletDistribution || {});
      } catch {
        setData({});
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const outletCounts = data[selectedTopic] || {};
  const sortedOutlets = Object.entries(outletCounts)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 8);

  if (loading) {
    return <div className="h-full flex items-center justify-center text-sm">Loading...</div>;
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header row */}
      <div className="flex items-center justify-between py-1 px-1 mb-2">
        <div className="text-xs font-semibold text-gray-700 truncate">
          {formatTopic(selectedTopic)} ({Object.keys(outletCounts).length} outlets)
        </div>
        <Select value={selectedTopic} onValueChange={setSelectedTopic}>
          <SelectTrigger className="w-24 h-7 text-xs border-gray-200">
            <SelectValue />
          </SelectTrigger>
          <SelectContent side="top" align="end" className="w-24">
            {Object.keys(data).slice(0, 8).map((topic) => (
              <SelectItem key={topic} value={topic}>
                {formatTopic(topic)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto space-y-1 px-1 scrollbar-hide">
        {sortedOutlets.map(([outlet, count], idx) => (
          <div 
            key={outlet} 
            className="flex items-center justify-between py-1.5 px-2 text-xs bg-white/80 hover:bg-white rounded-md border border-gray-100 hover:border-gray-200 transition-colors h-8"
          >
            <span className="font-medium text-gray-900 truncate mr-2 flex-1 min-w-0">
              {outlet.length > 18 ? outlet.slice(0, 18) + '...' : outlet}
            </span>
            <span className="font-bold text-gray-800 bg-gray-100 px-2 py-0.5 rounded text-xs min-w-[36px] text-center">
              {count}
            </span>
          </div>
        ))}
        {sortedOutlets.length === 0 && (
          <div className="flex items-center justify-center text-gray-500 text-xs h-full py-4">
            No data
          </div>
        )}
      </div>
    </div>
  );
}
