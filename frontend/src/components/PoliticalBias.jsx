import { HashLoader } from 'react-spinners';
import { normalizeBias } from "@/utils/biasNormalizer";

const PoliticalBias = ({ politicalBiasResult }) => {
  if (!politicalBiasResult || !Object.keys(politicalBiasResult).length) {
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

  const rating = politicalBiasResult.rating;
  const topicsCovered = politicalBiasResult.topics?.covered || [];
  const topicsOmitted = politicalBiasResult.topics?.omitted || [];

  if (!rating) {
    return (
      <div className="text-center text-gray-500">
        Political bias rating is unavailable
      </div>
    );
  }

  const biasLevels = ['Left', 'Lean Left', 'Center', 'Lean Right', 'Right'];
  const normalizedBias = normalizeBias(rating).replace(/-/g, ' ');

  return (
    <div className="space-y-4">
      {/* Political Bias Scale */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="font-semibold text-base mb-3 text-gray-700">Political Bias Rating</div>
        <div className="flex gap-2 justify-between">
          {biasLevels.map((label) => {
            const isActive = normalizedBias === label.toLowerCase();
            return (
              <div
                key={label}
                className={`flex-1 min-w-0 text-center py-2 px-1 rounded-md text-xs sm:text-sm font-medium transition-all leading-tight break-words ${
                  isActive
                    ? `bg-white text-black shadow-md scale-105 ring-2 ring-offset-1 ring-black`
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
          {topicsCovered.length > 0 ? (
            <ul className="space-y-2">
              {topicsCovered.map((topic, index) => (
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
          {topicsOmitted.length > 0 ? (
            <ul className="space-y-2">
              {topicsOmitted.map((topic, index) => (
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
