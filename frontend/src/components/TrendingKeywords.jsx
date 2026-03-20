import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import get_api from "@/config/config";
import axios from "axios";
import { Button } from "@/components/ui/button";

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
  const navigate = useNavigate();

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

  const handleKeywordClick = (keyword) => {
    navigate(`/keywords/${encodeURIComponent(keyword)}`); 
  };

  return (
    <div className="h-full p-2">
      {topKeywords.length === 0 ? (
        <div className="h-full flex items-center justify-center text-lg">
          Loading...
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-none">
            {topKeywords.slice(0, 8).map((keyword, index) => (
              <Button
                key={index}
                className="p-4 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 transition-all duration-200 rounded-lg shadow-sm border border-blue-100 flex flex-col items-center justify-center h-[72px] w-full text-base font-semibold text-gray-900 leading-[1.1] text-center whitespace-normal word-break-keep-all overflow-wrap-anywhere"
                variant="ghost"  
                onClick={() => handleKeywordClick(keyword)}
              >
                <span className="w-full line-clamp-2">{titleCase(keyword)}</span>
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
