import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { HashLoader } from 'react-spinners';

const PoliticalBias = ({ url, title, content }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!url || !title || !content) return;

    const fetchPoliticalBias = async () => {
      try {
        setLoading(true);

        // Extract site from URL
        const urlObj = new URL(url);
        const site = urlObj.hostname;

        // Call rate_bias
        const rateResponse = await axios.get('${api}/biasengine/rate_bias', {
          params: {
            site: site,
            title: title,
            page_text: content
          }
        });
        const bias = rateResponse.data.rating;

        // Call get_topics
        const topicsResponse = await axios.get('${api}/biasengine/get_topics', {
          params: {
            site: site,
            title: title,
            page_text: content
          }
        });
        const topics = topicsResponse.data.topics;

        // Combine
        const combinedData = {
          bias: bias,
          topics_covered: topics.covered || [],
          topics_omitted: topics.omitted || []
        };

        setData(combinedData);
      } catch (error) {
        console.error('Error fetching political bias data:', error);
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
        No data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Political Bias */}
      <div>
        <div className="font-semibold text-lg mb-2">Political Bias</div>
        <p className="text-base">{data.bias || 'N/A'}</p>
      </div>

      {/* Topics Covered */}
      <div>
        <div className="font-semibold text-lg mb-2">Topics Covered</div>
        {data.topics_covered && data.topics_covered.length > 0 ? (
          <ul className="list-disc list-inside space-y-1 ml-4">
            {data.topics_covered.map((topic, index) => (
              <li key={index} className="text-base">{topic}</li>
            ))}
          </ul>
        ) : (
          <p className="text-base text-gray-500">No topics covered identified</p>
        )}
      </div>

      {/* Topics Omitted */}
      <div>
        <div className="font-semibold text-lg mb-2">Topics Omitted</div>
        {data.topics_omitted && data.topics_omitted.length > 0 ? (
          <ul className="list-disc list-inside space-y-1 ml-4">
            {data.topics_omitted.map((topic, index) => (
              <li key={index} className="text-base">{topic}</li>
            ))}
          </ul>
        ) : (
          <p className="text-base text-gray-500">No topics omitted identified</p>
        )}
      </div>
    </div>
  );
};

export default PoliticalBias;
