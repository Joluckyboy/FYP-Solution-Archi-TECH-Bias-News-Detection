import { useEffect, useMemo, useState } from "react";
import get_api from "@/config/config";
import axios from "axios";

const titleCase = (value) => {
  if (typeof value !== "string") return "";
  return value
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
};

export default function TrendingKeywords() {
  const [keywords, setKeywords] = useState([]);

  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      try {
        const api = await get_api();
        const res = await axios.get(`${api}/application/visualisations`);

        const raw = res?.data?.trendingKeywords;

        // Accept BOTH shapes:
        // 1) ["keyword", "another keyword"]
        // 2) [{ term: "keyword" }, ...]
        const normalized = Array.isArray(raw)
          ? raw
              .map((k) => {
                if (typeof k === "string") return k;
                if (k && typeof k === "object" && typeof k.term === "string") return k.term;
                return null;
              })
              .filter((k) => typeof k === "string" && k.trim().length > 0)
          : [];

        if (!cancelled) setKeywords(normalized);
      } catch {
        if (!cancelled) setKeywords([]);
      }
    };

    fetchData();
    return () => {
      cancelled = true;
    };
  }, []);

  const topKeywords = useMemo(() => keywords.slice(0, 8), [keywords]);

  return (
    <div className="h-full p-2 max-h-[340px] overflow-hidden">
      {topKeywords.length === 0 ? (
        <div className="h-full flex items-center justify-center text-sm text-gray-500">
          No trending keywords yet.
        </div>
      ) : (
          <div className="space-y-4 pt-2">
          {/* Row 1: Keywords 1-4 */}
          <div className="grid grid-cols-4 gap-4">
            {topKeywords.slice(0, 4).map((keyword, index) => (
              <div
                key={index}
                className="p-3 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 transition-all duration-200 rounded-lg shadow-sm border border-blue-100 flex items-center justify-center min-h-[60px] text-lg font-semibold text-gray-900 leading-tight truncate"
              >
                {titleCase(keyword)}
              </div>
            ))}
          </div>
          
          {/* Row 2: Keywords 5-8 */}
          <div className="grid grid-cols-4 gap-4">
            {topKeywords.slice(4, 8).map((keyword, index) => (
              <div
                key={index + 4}
                className="p-3 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 transition-all duration-200 rounded-lg shadow-sm border border-blue-100 flex items-center justify-center min-h-[60px] text-lg font-semibold text-gray-900 leading-tight truncate"
              >
                {titleCase(keyword)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
