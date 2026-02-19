import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import get_api from "@/config/config";
import axios from "axios";

const BUCKET_ORDER = ['left', 'leaning-left', 'center', 'leaning-right', 'right'];
const BUCKET_LABELS = {
  left: 'Left',
  'leaning-left': 'Lean Left',
  center: 'Center',
  'leaning-right': 'Lean Right',
  right: 'Right',
};
const BUCKET_COLORS = {
  left: 'bg-blue-200 border-blue-300',
  'leaning-left': 'bg-blue-100 border-blue-200',
  center: 'bg-gray-100 border-gray-200',
  'leaning-right': 'bg-red-100 border-red-200',
  right: 'bg-red-200 border-red-300',
};

export default function TopicOutletBias() {
  const [data, setData] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState('general-news');
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[500px]">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (error || !data?.topicOutletBiasGroups) {
    return (
      <div className="flex items-center justify-center h-full min-h-[500px]">
        <div className="text-lg text-red-500">{error || 'No data available'}</div>
      </div>
    );
  }

  const biasGroups = data.topicOutletBiasGroups?.[selectedTopic] || {};
  const allOutlets = BUCKET_ORDER.flatMap(bucket => biasGroups[bucket] || []);
  const totalOutlets = new Set(allOutlets.map(item => item.outlet)).size;
  const totalArticles = allOutlets.reduce((sum, item) => sum + item.count, 0);
  const getSortedOutlets = (outlets) => {
    return outlets
      .sort((a, b) => a.outlet.localeCompare(b.outlet))
      .slice(0, 8); 
  };

  return (
    <div className="h-full flex flex-col hover:none p-6">
      {/* Header - Fixed height */}
      <div className="flex flex-row items-start justify-between mb-6 h-20 hover:none">
        <div className="text-left hover:none">
          <div className="text-2xl font-bold mb-1 hover:none">
            {formatTopic(selectedTopic)}
          </div>
          <div className="text-lg text-muted-foreground hover:none">
            {totalOutlets} unique outlets
          </div>
        </div>
        <Select value={selectedTopic} onValueChange={setSelectedTopic}>
          <SelectTrigger className="w-56 h-10 hover:none">
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

      {/* Content */}
      <div className="flex-1 grid grid-cols-5 gap-4 items-start hover:none">
        {BUCKET_ORDER.map((bucket) => {
          const outlets = getSortedOutlets(biasGroups[bucket] || []);
          const bucketArticles = outlets.reduce((sum, item) => sum + item.count, 0);
          const percentage = totalArticles > 0 ? ((bucketArticles / totalArticles) * 100).toFixed(1) : '0.0';

          return (
            <div key={bucket} className="flex flex-col gap-4 h-full hover:none">
              {/* ✅ LABEL BOX */}
              <div className={`w-full h-24 p-4 rounded-xl border shadow-sm flex flex-col justify-center text-center ${BUCKET_COLORS[bucket]} hover:none`}>
                <div className="text-lg font-black tracking-wide hover:none"> 
                  {BUCKET_LABELS[bucket].charAt(0).toUpperCase() + BUCKET_LABELS[bucket].slice(1).toLowerCase()}
                </div>
                <div className="text-sm font-mono text-gray-600 mt-1 hover:none">
                  {percentage}%
                </div>
              </div>
              
              {/* ✅ OUTLET BOX */}
              <div className={`w-full h-56 p-3 rounded-xl border shadow-sm overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100 ${BUCKET_COLORS[bucket]} hover:none`}>
                {outlets.length > 0 ? (
                  outlets.map((item, idx) => (
                    <div 
                      key={idx} 
                      className="truncate py-2 hover:none border-b border-gray-100/50 last:border-b-0 text-base leading-relaxed"  // text-base + py-2
                      style={{ lineHeight: '1.4' }}  // Comfortable spacing
                    >
                      {item.outlet}
                    </div>
                  ))
                ) : (
                  <div className="h-full flex items-center justify-center text-muted-foreground italic text-lg">
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
