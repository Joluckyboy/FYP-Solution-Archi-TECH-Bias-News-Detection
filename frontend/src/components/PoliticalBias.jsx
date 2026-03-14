import { useEffect, useState } from 'react';
import axios from 'axios';
import { HashLoader } from 'react-spinners';
import { get_bias } from '../config/config';

const cache = {};

const PoliticalBias = ({ url, title, content }) => {
  const [data, setData] = useState(cache[url] || null);
  const [loading, setLoading] = useState(!cache[url]);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);

  useEffect(() => {
    if (!url || !title || !content) return;
    if (cache[url]) return;

    const fetchPoliticalBias = async () => {
      try {
        setLoading(true);
        setError(null);
        setWarning(null);

        // Extract site from URL
        const urlObj = new URL(url);
        const site = urlObj.hostname;
        const payload = {
          site,
          title,
          page_text: content,
        };

        // Call rate_bias
        const biasApi = await get_bias();
        const rateResponse = await axios.post(`${biasApi}/biasengine/rate_bias`, payload);
        if (!rateResponse?.data?.rating) {
          throw new Error(rateResponse?.data?.message || 'Political bias rating is unavailable');
        }
        const bias = rateResponse.data.rating;

        let topics = { covered: [], omitted: [] };
        try {
          const topicsResponse = await axios.post(`${biasApi}/biasengine/get_topics`, payload);
          const topicsData = topicsResponse?.data?.topics;
          if (topicsData && typeof topicsData === 'object') {
            topics = topicsData;
          } else {
            setWarning(topicsResponse?.data?.message || 'Topics analysis unavailable for this article');
          }

          if (topicsResponse?.data?.warning) {
            setWarning(topicsResponse.data.warning);
          }
        } catch (topicsError) {
          console.warn('Topics analysis unavailable:', topicsError);
          setWarning(topicsError?.response?.data?.message || 'Topics analysis unavailable for this article');
        }

        // Combine
        const combinedData = {
          bias: bias,
          topics_covered: topics.covered || [],
          topics_omitted: topics.omitted || []
        };

        cache[url] = combinedData;
        setData(combinedData);
      } catch (error) {
        console.error('Error fetching political bias data:', error);
        setError(error?.response?.data?.message || error?.message || 'Failed to fetch political bias data');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchPoliticalBias();
  }, [url, title, content]);

  if (loading) {
    return (
      <div className="text-center flex flex-col items-center">
        <br />
        Analysis in progress
        <br />
        <br />
        <HashLoader color="#1E5EDD" loading={true} size={50} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center text-gray-500">
        {error || 'No data available'}
      </div>
    );
  }

  const biasLevels = ['Left', 'Leaning left', 'Center', 'Leaning right', 'Right'];

  const normalizedBias = data.bias?.toLowerCase().trim().replace(/[-_]/g, ' ');

  return (
    <div className="space-y-4">
      {warning && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          {warning}
        </div>
      )}

      {/* Political Bias Scale */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="font-semibold text-base mb-3 text-gray-700">Political Bias Rating</div>
        <div className="flex gap-2 justify-between">
          {biasLevels.map((label) => {
            const isActive = normalizedBias === label.toLowerCase();
            return (
              <div
                key={label}
                className={`flex-1 text-center py-2 px-1 rounded-md text-sm font-medium transition-all ${
                  isActive
                    ? `bg-blue-600 text-white shadow-md scale-105 ring-2 ring-offset-1 ring-blue-400`
                    : 'bg-gray-100 text-gray-300'
                }`}
              >
                {label}
              </div>
            );
          })}
        </div>
      </div>

      {/* Topics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Topics Covered */}
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 shadow-sm">
          <div className="font-semibold text-base mb-3 text-green-800">Topics Covered</div>
          {data.topics_covered && data.topics_covered.length > 0 ? (
            <ul className="space-y-2">
              {data.topics_covered.map((topic, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-green-900">
                  <span className="mt-1 h-2 w-2 rounded-full bg-green-500 shrink-0" />
                  {topic}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No topics covered identified</p>
          )}
        </div>

        {/* Topics Omitted */}
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 shadow-sm">
          <div className="font-semibold text-base mb-3 text-rose-800">Topics Omitted</div>
          {data.topics_omitted && data.topics_omitted.length > 0 ? (
            <ul className="space-y-2">
              {data.topics_omitted.map((topic, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-rose-900">
                  <span className="mt-1 h-2 w-2 rounded-full bg-rose-500 shrink-0" />
                  {topic}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No topics omitted identified</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PoliticalBias;
