import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import get_api from "@/config/config";
import axios from "axios";

const bucketOrder = ["left", "leaning-left", "center", "leaning-right", "right"];
const bucketLabels = { 
  left: "Left", 
  "leaning-left": "Lean Left", 
  center: "Center", 
  "leaning-right": "Lean Right", 
  right: "Right" 
};
const bucketColors = { 
  left: "bg-blue-200", 
  "leaning-left": "bg-blue-100", 
  center: "bg-purple-100", 
  "leaning-right": "bg-red-100", 
  right: "bg-red-200" 
};

export default function OutletBiasChart() {
  const [groups, setGroups] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError("");
        const api = await get_api();
        const res = await axios.get(`${api}/application/visualisations`);
        setGroups(res.data.outletBiasGroups || {});
      } catch (err) {
        setError("Failed to load bias data");
        console.error("Visualisations API error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg">Loading bias chart...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="grid grid-cols-5 gap-4 flex-1">
        {bucketOrder.map((bucket) => {
          const outlets = groups[bucket] || [];
          return (
            <Card key={bucket} className={`h-full ${bucketColors[bucket]}`}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-gray-800">
                  {bucketLabels[bucket]}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 p-4">
                {outlets.length === 0 ? (
                  <p className="text-xs text-gray-500">No outlets</p>
                ) : (
                  <div className="space-y-1 max-h-64 overflow-y-auto">
                    {outlets.map((outlet, idx) => (
                      <div key={idx} className="text-xs truncate">
                        {outlet}
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-2 text-xs text-gray-600">
                  {outlets.length} outlets
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
