import React, { useEffect, useState } from "react";
import get_api from "@/config/config";
import axios from "axios";

export default function TrendingKeywords() {
  const [keywords, setKeywords] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const api = await get_api();
        const res = await axios.get(`${api}/application/visualisations`);
        setKeywords(res.data.trendingKeywords || []);
      } catch {
        setKeywords([]);
      }
    };
    fetchData();
  }, []);

  const titleCase = (str) => 
    str.split(' ')
       .map(word => word.charAt(0).toUpperCase() + word.slice(1))
       .join(' ');

  return (
    <div className="grid grid-cols-2 gap-3 h-full p-2 max-h-[340px] overflow-hidden">
      {keywords.slice(0, 8).map((keyword, index) => (
        <div 
          key={index}
          className="p-3 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 
                     hover:from-blue-100 hover:to-purple-100 transition-all duration-200 
                     rounded-lg shadow-sm border border-blue-100 flex items-center justify-center min-h-[60px]
                     text-lg font-semibold text-gray-900 leading-tight truncate"
          title={titleCase(keyword.term)}  // Full text on hover
        >
          {titleCase(keyword.term)}
        </div>
      ))}
    </div>
  );
}
