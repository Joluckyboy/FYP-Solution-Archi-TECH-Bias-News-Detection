import { useEffect, useState } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import get_api from "@/config/config";
import axios from "axios";

const BUCKET_ORDER = ['left', 'leaning-left', 'center', 'leaning-right', 'right'];
const BUCKET_LABELS = { left: 'Left', 'leaning-left': 'Lean Left', center: 'Center', 'leaning-right': 'Lean Right', right: 'Right' };

const BUCKET_COLORS = {
  left: 'bg-blue-200 border-blue-300',
  'leaning-left': 'bg-blue-100 border-blue-200',
  center: 'bg-purple-100 border-purple-200',
  'leaning-right': 'bg-red-100 border-red-200',
  right: 'bg-red-200 border-red-300',
};

export default function TopicOutletBias() {
  const [data, setData] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const formatTopic = (topic) => {
    return topic
      .replace(/-/g, ' ')
      .replace(/general news/gi, 'General News')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const api = await get_api();
        const res = await axios.get(`${api}/application/visualisations`);
        setData(res.data);
      } catch (err) {
        setError('Failed to load topic bias data');
        console.error('Visualisations API error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    const topics = Object.keys(data?.topicOutletDistribution || {});
    if (topics.length > 0 && selectedTopic === "") {
      setSelectedTopic(topics[0]);
    }
  }, [data?.topicOutletDistribution, selectedTopic]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (error || !data?.topicOutletBiasGroups) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="text-lg text-red-500">{error || 'No data available'}</div>
      </div>
    );
  }

  const biasGroups = data.topicOutletBiasGroups?.[selectedTopic] || {};
  const allOutlets = BUCKET_ORDER.flatMap(bucket => biasGroups[bucket] || []);
  const totalOutlets = new Set(allOutlets.map(item => item.outlet)).size;
  const totalArticles = allOutlets.reduce((sum, item) => sum + item.count, 0);

  const getSortedOutlets = (outlets) =>
    outlets.sort((a, b) => a.outlet.localeCompare(b.outlet));

  return (
    <div className="flex flex-col sm:px-6 gap-4 sm:gap-6">

      {/* Header */}
      <div className="flex flex-row items-start justify-between gap-4 flex-wrap">
        <div className="text-left">
          <div className="text-xl sm:text-2xl font-bold mb-1">
            {formatTopic(selectedTopic)}
          </div>
          <div className="text-base sm:text-lg text-muted-foreground">
            {totalOutlets} unique outlets
          </div>
        </div>
        <Select value={selectedTopic} onValueChange={setSelectedTopic}>
          <SelectTrigger className="w-48 sm:w-56 h-10">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.keys(data.topicOutletDistribution || {}).map((topic) => (
              <SelectItem key={topic} value={topic}>
                {formatTopic(topic)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 sm:gap-4 items-start">
        {BUCKET_ORDER.map((bucket) => {
          const outlets = getSortedOutlets(biasGroups[bucket] || []);
          const bucketArticles = outlets.reduce((sum, item) => sum + item.count, 0);
          const percentage = totalArticles > 0
            ? ((bucketArticles / totalArticles) * 100).toFixed(1)
            : '0.0';

          return (
            <div key={bucket} className="flex flex-col gap-3 sm:gap-4">

              {/* Label Box */}
              <div className={`w-full h-16 sm:h-24 p-2 sm:p-4 rounded-xl border shadow-sm flex flex-col items-center justify-center text-center ${BUCKET_COLORS[bucket]}`}>
                <div className="text-sm sm:text-2xl font-black tracking-wide leading-tight">
                  {BUCKET_LABELS[bucket]}
                </div>
                <div className="text-xs sm:text-sm font-mono text-gray-600 mt-0.5 sm:mt-1">
                  {percentage}%
                </div>
              </div>

              {/* Outlet Box */}
              <div
                className={`w-full p-2 sm:p-3 rounded-xl border shadow-sm overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent ${BUCKET_COLORS[bucket]}`}
                style={{ height: 'calc(5.5 * 2.25rem)' }}
              >
                {outlets.length > 0 ? (
                  outlets.map((item, idx) => (
                    <div
                      key={idx}
                      className="py-1.5 border-b border-gray-100/50 last:border-b-0 text-xs sm:text-sm leading-snug break-words"
                    >
                      {item.outlet}
                    </div>
                  ))
                ) : (
                  <div className="h-full flex items-center justify-center text-muted-foreground italic text-sm sm:text-lg">
                    No outlets
                  </div>
                )}
              </div>

            </div>
          );
        })}
      </div>
    </div>
  );
}
